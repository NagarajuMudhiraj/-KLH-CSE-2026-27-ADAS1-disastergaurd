/**
 * ADAS Computer Vision Detection Filter & Temporal Persistence Engine
 * Enforces Sections 12, 13, 14, 15, 16, 17, 31, 35:
 * - Confidence thresholding (filters noisy low-confidence frames)
 * - Temporal persistence tracking (requires 3-4 consecutive frames before declaring event)
 * - Duplicate suppression (spatial + temporal cooldown prevents spamming admin)
 * - Direct Driver Popup alerts (short, clear: pothole depth, distance)
 * - Serious hazard filtering: Only serious hazards (Flood, Fire, Smoke, Pothole, Damage) sent to admin;
 *   ordinary pedestrians/cars trigger local driver warnings only.
 */

import api from './api';

const SERIOUS_HAZARD_TYPES = [
  'flood',
  'fire',
  'smoke',
  'pothole',
  'road damage',
  'landslide',
  'accident',
  'road block'
];

export class DetectionFilter {
  constructor(options = {}) {
    this.minConfidence = options.minConfidence || 0.55;
    this.persistenceThreshold = options.persistenceThreshold || 3; // N frames
    this.cooldownSeconds = options.cooldownSeconds || 45; // seconds before re-dispatching same hazard at same location
    
    // Track observation history: { [category]: { count: number, maxConf: number, lastSeen: timestamp } }
    this.persistenceMap = new Map();
    
    // Cooldown map: key = `${type}_${latRound}_${lngRound}`, value = timestamp
    this.dispatchedCooldowns = new Map();
  }

  /**
   * Resets persistence streaks (e.g. when camera is closed)
   */
  reset() {
    this.persistenceMap.clear();
  }

  /**
   * Normalizes raw YOLO class name into canonical hazard key
   */
  normalizeCategory(rawName) {
    if (!rawName) return 'hazard';
    const n = String(rawName).toLowerCase();
    if (n.includes('pothole') || n.includes('pit')) return 'pothole';
    if (n.includes('flood') || n.includes('water')) return 'flood';
    if (n.includes('fire') || n.includes('flame')) return 'fire';
    if (n.includes('smoke') || n.includes('haze')) return 'smoke';
    if (n.includes('person') || n.includes('pedestrian') || n.includes('victim')) return 'pedestrian';
    if (n.includes('vehicle') || n.includes('car') || n.includes('truck')) return 'vehicle';
    if (n.includes('damage') || n.includes('crack')) return 'road damage';
    return n;
  }

  /**
   * Evaluates detections from a single video/camera frame.
   * 
   * @param {Array} detections - List of YOLO detections with bbox, confidence, class_name, depth_cm, distance_m
   * @param {Object} currentGps - { lat, lng }
   * @param {string} snapshotBase64 - Optional base64 frame preview
   * @returns {Object} { driverAlert: Object|null, adminEventDispatched: Object|null, persistentHazards: Array }
   */
  async processFrame(detections = [], currentGps = null, snapshotBase64 = null) {
    const now = Date.now();
    const frameClasses = new Set();
    let bestDriverCandidate = null;
    let highestDriverSeverity = 0;

    // 1. Process detections in current frame
    for (const det of detections) {
      const conf = det.confidence || 0;
      if (conf < this.minConfidence) continue;

      const category = this.normalizeCategory(det.class_name);
      frameClasses.add(category);

      const existing = this.persistenceMap.get(category) || { count: 0, maxConf: 0, lastSeen: 0, lastDet: null };
      const newCount = existing.count + 1;
      const newMaxConf = Math.max(existing.maxConf, conf);

      this.persistenceMap.set(category, {
        count: newCount,
        maxConf: newMaxConf,
        lastSeen: now,
        lastDet: det
      });

      // Priority calculation for immediate driver warnings
      let priorityScore = conf * 10;
      if (category === 'pothole') priorityScore += 15;
      if (category === 'flood') priorityScore += 18;
      if (category === 'fire') priorityScore += 20;
      if (category === 'pedestrian' && (det.distance_m || 20) < 15) priorityScore += 25;

      if (priorityScore > highestDriverSeverity) {
        highestDriverSeverity = priorityScore;
        bestDriverCandidate = {
          category,
          det,
          streak: newCount,
          confidence: conf
        };
      }
    }

    // 2. Decay / clear classes not present in this frame
    for (const [cat, data] of this.persistenceMap.entries()) {
      if (!frameClasses.has(cat)) {
        if (now - data.lastSeen > 2000) {
          // If absent for >2 seconds, decay streak
          data.count = Math.max(0, data.count - 1);
          if (data.count === 0) {
            this.persistenceMap.delete(cat);
          }
        }
      }
    }

    // 3. Section 13: Build Driver Alert Popup if persistent or high-risk
    let driverAlert = null;
    if (bestDriverCandidate && bestDriverCandidate.streak >= 2) {
      const { category, det } = bestDriverCandidate;
      const depthVal = det.depth_cm || 8;
      const distVal = det.distance_m || 6;

      let title = `⚠ Hazard detected ahead`;
      let details = [];

      switch (category) {
        case 'pothole':
          title = `⚠ Pothole detected ahead`;
          details.push(`Depth: ~${Math.round(depthVal)} cm`);
          details.push(`Distance: ~${Math.round(distVal)} m`);
          break;
        case 'flood':
          title = `⚠ Flood detected ahead`;
          details.push(`Distance: ~${Math.round(distVal)} m`);
          break;
        case 'pedestrian':
          title = `⚠ Pedestrian ahead`;
          details.push(`Distance: ~${Math.round(distVal)} m`);
          break;
        case 'road damage':
          title = `⚠ Road damage detected ahead`;
          details.push(`Distance: ~${Math.round(distVal)} m`);
          break;
        case 'fire':
          title = `⚠ Fire hazard detected ahead`;
          details.push(`Distance: ~${Math.round(distVal)} m`);
          break;
        case 'smoke':
          title = `⚠ Dense smoke plume ahead`;
          details.push(`Distance: ~${Math.round(distVal)} m`);
          break;
        default:
          title = `⚠ ${det.class_name || 'Hazard'} detected ahead`;
          details.push(`Distance: ~${Math.round(distVal)} m`);
      }

      driverAlert = {
        title,
        category,
        depth_cm: det.depth_cm,
        distance_m: det.distance_m,
        confidence: bestDriverCandidate.confidence,
        detailsText: details.join(' · '),
        timestamp: new Date().toISOString()
      };
    }

    // 4. Section 16 & 17: Forward serious persistent hazards to Admin
    let adminEventDispatched = null;

    if (currentGps && currentGps.lat && currentGps.lng) {
      for (const [cat, data] of this.persistenceMap.entries()) {
        const isSerious = SERIOUS_HAZARD_TYPES.some(s => cat.includes(s));
        // Section 17: Ordinary pedestrians and vehicles do NOT go to admin
        if (!isSerious) continue;

        // Section 12: Requires temporal persistence (e.g. 3 consecutive evaluation frames)
        if (data.count >= this.persistenceThreshold) {
          // Section 35: Deduplication check
          const latRound = currentGps.lat.toFixed(3);
          const lngRound = currentGps.lng.toFixed(3);
          const dedupKey = `${cat}_${latRound}_${lngRound}`;
          const lastDispatched = this.dispatchedCooldowns.get(dedupKey) || 0;

          if (now - lastDispatched > this.cooldownSeconds * 1000) {
            this.dispatchedCooldowns.set(dedupKey, now);

            const payload = {
              source: 'AI',
              type: cat,
              confidence: parseFloat(data.maxConf.toFixed(2)),
              latitude: parseFloat(currentGps.lat.toFixed(5)),
              longitude: parseFloat(currentGps.lng.toFixed(5)),
              timestamp: new Date().toISOString(),
              severity: data.maxConf > 0.80 ? 'CRITICAL' : 'HIGH',
              depth_cm: data.lastDet?.depth_cm || (cat === 'pothole' ? 8.0 : null),
              distance_m: data.lastDet?.distance_m || 6.0,
              image_base64: snapshotBase64 || null,
              status: 'PENDING_REVIEW'
            };

            try {
              const res = await api.reportAIDetectedHazard(payload);
              adminEventDispatched = {
                id: res?.id,
                category: cat,
                status: 'PENDING_REVIEW',
                confidence: payload.confidence
              };
            } catch (err) {
              console.warn('AI hazard forward warning:', err.message);
            }
          }
        }
      }
    }

    return {
      driverAlert,
      adminEventDispatched,
      activeStreaks: Array.from(this.persistenceMap.entries()).map(([k, v]) => ({
        category: k,
        streak: v.count,
        confidence: v.maxConf
      }))
    };
  }
}

export const detectionFilter = new DetectionFilter();
export default detectionFilter;
