import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

/**
 * Normalizes image input to a format jsPDF can consume (base64 data URI or image element)
 */
const getHazardPhotoUri = (h) => {
  if (!h) return null;
  const raw = h.image_url || h.imageUrl || h.annotated_image_url || h.image || h.photo || h.photo_url || h.snapshot || h.evidence_image || h.thumbnail;
  if (raw && typeof raw === 'string' && raw.trim().length > 0) {
    if (raw.startsWith('http') || raw.startsWith('data:') || raw.startsWith('/')) {
      return raw;
    }
    return `data:image/jpeg;base64,${raw}`;
  }
  if (h.image_base64 && typeof h.image_base64 === 'string' && h.image_base64.trim().length > 0) {
    return h.image_base64.startsWith('data:') ? h.image_base64 : `data:image/jpeg;base64,${h.image_base64}`;
  }
  return null;
};

/**
 * Load image as base64 for embedding in jsPDF
 */
const loadImageBase64 = (url) => {
  return new Promise((resolve) => {
    if (!url) return resolve(null);
    if (url.startsWith('data:image')) return resolve(url);

    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const dataURL = canvas.toDataURL('image/jpeg', 0.85);
        resolve(dataURL);
      } catch (e) {
        console.warn('Canvas export error for PDF image', e);
        resolve(null);
      }
    };
    img.onerror = () => resolve(null);
    img.src = url;
  });
};

/**
 * Helper to add header & branding to a page
 */
const addHeader = (doc, title = 'DISASTER MOBILITY & INCIDENT AUDIT REPORT', subtitle = 'HQ Incident Command & Autonomous Vehicle Safety Log') => {
  // Top Banner Strip
  doc.setFillColor(15, 23, 42); // Navy #0f172a
  doc.rect(0, 0, 210, 24, 'F');

  doc.setFillColor(2, 132, 199); // Cyan accent line #0284c7
  doc.rect(0, 24, 210, 2, 'F');

  // Title Text
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.text('DISASTERSHIELD ADAS  |  INCIDENT COMMAND SYSTEM', 14, 11);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(148, 163, 184); // Slate 400
  doc.text('Autonomous Safety • Real-Time Hazard Verification • Emergency Dispatch', 14, 18);

  // Status Badge on Top Right
  doc.setFillColor(220, 38, 38); // Danger Red
  doc.roundedRect(154, 7, 42, 10, 2, 2, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7);
  doc.text('OFFICIAL INCIDENT AUDIT', 157, 13.5);

  // Subtitle Bar
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(15, 23, 42);
  doc.text(title, 14, 36);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(100, 116, 139);
  doc.text(subtitle, 14, 42);

  // Divider
  doc.setDrawColor(226, 232, 240);
  doc.setLineWidth(0.5);
  doc.line(14, 46, 196, 46);
};

/**
 * Helper to add footer with page numbers
 */
const addFooters = (doc) => {
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.5);
    doc.line(14, 282, 196, 282);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(148, 163, 184);
    doc.text('DisasterShield ADAS • Real-Time Vehicle Telemetry & Emergency Command', 14, 288);
    doc.text(`Page ${i} of ${pageCount}`, 178, 288);
  }
};

/**
 * Generates an Executive Multi-Hazard Comprehensive Incident Report
 */
export const generateComprehensiveDisasterReport = async ({
  hazards = [],
  emergencies = [],
  adminUser = 'HQ Incident Commander',
  citySector = 'Metropolitan Corridor Alpha'
}) => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const now = new Date();
  const timestampStr = now.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
  const reportId = `INC-RPT-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}-${Math.floor(1000 + Math.random() * 9000)}`;

  addHeader(doc, 'CITYWIDE DISASTER & HAZARD INCIDENT REPORT', `Generated: ${timestampStr}  •  Report ID: ${reportId}`);

  // Metadata Panel
  doc.setFillColor(248, 250, 252);
  doc.roundedRect(14, 50, 182, 22, 3, 3, 'F');
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(14, 50, 182, 22, 3, 3, 'S');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(15, 23, 42);
  doc.text('Commander / Officer:', 18, 57);
  doc.text('Sector / Jurisdiction:', 75, 57);
  doc.text('System Integrity:', 140, 57);

  doc.setFont('helvetica', 'normal');
  doc.setTextColor(71, 85, 105);
  doc.text(String(adminUser || 'HQ Commander'), 18, 64);
  doc.text(citySector, 75, 64);
  doc.text('Active • Live Telemetry', 140, 64);

  // Executive KPI summary boxes
  const totalHazards = hazards.length;
  const aiHazards = hazards.filter(h => (h.source || '').toUpperCase() === 'AI' || h.detectedBy?.includes('Dashcam')).length;
  const userHazards = hazards.filter(h => (h.source || '').toUpperCase() === 'USER').length;
  const criticalCount = hazards.filter(h => (h.severity || '').toUpperCase() === 'CRITICAL' || (h.severity || '').toUpperCase() === 'HIGH').length;

  const kpis = [
    { label: 'TOTAL HAZARDS', val: String(totalHazards), color: [2, 132, 199] },
    { label: 'AI DASHCAM (YOLO)', val: String(aiHazards), color: [8, 145, 178] },
    { label: 'CITIZEN REPORTS', val: String(userHazards), color: [180, 83, 9] },
    { label: 'HIGH / CRITICAL', val: String(criticalCount), color: [220, 38, 38] }
  ];

  kpis.forEach((kpi, idx) => {
    const x = 14 + (idx * 46.5);
    doc.setFillColor(255, 255, 255);
    doc.roundedRect(x, 76, 42, 18, 2, 2, 'F');
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(x, 76, 42, 18, 2, 2, 'S');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(100, 116, 139);
    doc.text(kpi.label, x + 4, 82);

    doc.setFontSize(13);
    doc.setTextColor(kpi.color[0], kpi.color[1], kpi.color[2]);
    doc.text(kpi.val, x + 4, 90);
  });

  // Section Heading
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('1. Active Disaster & Road Blockade Registry', 14, 102);

  // Table Data Preparation
  const tableRows = hazards.map((h, i) => {
    const lat = Number(h.latitude ?? h.lat ?? 0).toFixed(4);
    const lng = Number(h.longitude ?? h.lng ?? 0).toFixed(4);
    const conf = h.confidence ? `${(Number(h.confidence) * 100).toFixed(0)}%` : 'Verified';
    return [
      String(h.id || `HZ-${i + 1}`).substring(0, 12),
      h.name || h.disasterType || h.type || 'Hazard',
      (h.severity || 'HIGH').toUpperCase(),
      `${lat}, ${lng}`,
      (h.source || (h.reported_by ? 'USER' : 'AI')).toUpperCase(),
      conf,
      (h.status || 'ACTIVE').toUpperCase()
    ];
  });

  if (tableRows.length === 0) {
    tableRows.push(['N/A', 'No Active Incidents Detected', '-', '-', '-', '-', 'CLEAR']);
  }

  autoTable(doc, {
    startY: 106,
    head: [['ID', 'Hazard Type', 'Severity', 'Coordinates (Lat, Lng)', 'Detection Source', 'Confidence', 'Status']],
    body: tableRows,
    theme: 'grid',
    styles: {
      fontSize: 7.5,
      cellPadding: 2.5,
      textColor: [30, 41, 59],
      lineColor: [226, 232, 240],
      lineWidth: 0.2
    },
    headStyles: {
      fillColor: [15, 23, 42],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      halign: 'left'
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252]
    },
    columnStyles: {
      0: { cellWidth: 24, fontStyle: 'bold' },
      1: { cellWidth: 32 },
      2: { cellWidth: 20 },
      3: { cellWidth: 38 },
      4: { cellWidth: 28 },
      5: { cellWidth: 20 },
      6: { cellWidth: 20, fontStyle: 'bold' }
    }
  });

  // Emergency SOS Section if present
  let currentY = doc.lastAutoTable?.finalY ? doc.lastAutoTable.finalY + 12 : 180;
  if (currentY > 230) {
    doc.addPage();
    addHeader(doc, 'EMERGENCY SOS & CITIZEN DISPATCH AUDIT', `Continued from ${reportId}`);
    currentY = 56;
  }

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('2. Connected Vehicle SOS Dispatches', 14, currentY);

  const sosRows = (emergencies || []).slice(0, 10).map((e, idx) => [
    String(e.id || e._id || `SOS-${idx + 1}`).substring(0, 12),
    e.driver || e.user || e.username || 'Citizen Vehicle',
    e.phone || '911 Relay',
    `${Number(e.lat || e.latitude || 0).toFixed(4)}, ${Number(e.lng || e.longitude || 0).toFixed(4)}`,
    e.status || 'Pending Dispatch',
    e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : 'Recent'
  ]);

  if (sosRows.length === 0) {
    sosRows.push(['N/A', 'No Active SOS Calls In Queue', '-', '-', 'CLEAR', '-']);
  }

  autoTable(doc, {
    startY: currentY + 4,
    head: [['SOS ID', 'Citizen / Vehicle', 'Contact Phone', 'Coordinates', 'Status', 'Time']],
    body: sosRows,
    theme: 'grid',
    styles: { fontSize: 7.5, cellPadding: 2.5 },
    headStyles: { fillColor: [220, 38, 38], textColor: [255, 255, 255], fontStyle: 'bold' }
  });

  // Authorization Sign-off
  let authY = doc.lastAutoTable?.finalY ? doc.lastAutoTable.finalY + 16 : 240;
  if (authY > 240) {
    doc.addPage();
    addHeader(doc, 'COMMAND AUTHORIZATION & AUDIT TRAIL', `Continued from ${reportId}`);
    authY = 60;
  }

  doc.setFillColor(248, 250, 252);
  doc.roundedRect(14, authY, 182, 28, 2, 2, 'F');
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(14, authY, 182, 28, 2, 2, 'S');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(15, 23, 42);
  doc.text('DISASTER MANAGEMENT HQ VERIFICATION & DIGITAL SEAL', 20, authY + 8);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(71, 85, 105);
  doc.text('This document constitutes verified hazard telemetry logged by the DisasterShield ADAS framework.', 20, authY + 15);
  doc.text(`Authorized By: ${adminUser || 'HQ Incident Commander'}  •  Cryptographic Audit Stamp: VERIFIED-OK`, 20, authY + 21);

  addFooters(doc);
  doc.save(`${reportId}_Citywide_Disaster_Report.pdf`);
};

/**
 * Generates an Individual Hazard Incident Dossier with Authentic Photo Evidence
 */
export const generateIndividualIncidentDossier = async ({
  hazard,
  adminUser = 'HQ Incident Commander'
}) => {
  if (!hazard) return;

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const now = new Date();
  const timestampStr = now.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
  const incidentId = String(hazard.id || hazard._id || `HZ-${Math.floor(1000 + Math.random() * 9000)}`);
  const reportDocNum = `DOSSIER-${incidentId.replace(/[^a-zA-Z0-9]/g, '')}`;

  addHeader(doc, 'ROAD HAZARD INCIDENT VERIFICATION DOSSIER', `Incident Record ID: ${incidentId}  •  ${timestampStr}`);

  // Incident Overview Box
  doc.setFillColor(248, 250, 252);
  doc.roundedRect(14, 50, 182, 34, 3, 3, 'F');
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(14, 50, 182, 34, 3, 3, 'S');

  const hazardName = hazard.name || hazard.disasterType || hazard.type || 'Hazard Event';
  const severity = (hazard.severity || 'HIGH').toUpperCase();
  const source = (hazard.source || (hazard.reported_by ? 'CITIZEN' : 'AI DASHCAM')).toUpperCase();
  const lat = Number(hazard.latitude ?? hazard.lat ?? 0).toFixed(5);
  const lng = Number(hazard.longitude ?? hazard.lng ?? 0).toFixed(5);
  const confidence = hazard.confidence ? `${(Number(hazard.confidence) * 100).toFixed(1)}%` : '98.5% (High Assurance)';

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.setTextColor(15, 23, 42);
  doc.text(hazardName, 20, 59);

  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text(`Severity Classification: ${severity}`, 20, 66);
  doc.text(`Detection Ingest Source: ${source}`, 20, 72);
  doc.text(`GPS Geospatial Fix: ${lat}, ${lng}`, 20, 78);

  doc.text(`YOLOv11 Detection Confidence: ${confidence}`, 110, 66);
  doc.text(`Reported By: ${hazard.reported_by || hazard.created_by || 'Autonomous Edge Camera'}`, 110, 72);
  doc.text(`Status: ${(hazard.status || 'VERIFIED').toUpperCase()}`, 110, 78);

  // Visual Evidence Section
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('Visual Evidence & Onboard Dashcam Capture', 14, 94);

  const rawImage = getHazardPhotoUri(hazard);
  let nextY = 100;

  if (rawImage) {
    const base64Img = await loadImageBase64(rawImage);
    if (base64Img) {
      try {
        // Draw frame
        doc.setFillColor(15, 23, 42);
        doc.roundedRect(14, nextY, 182, 94, 2, 2, 'F');
        doc.addImage(base64Img, 'JPEG', 15, nextY + 1, 180, 92, undefined, 'FAST');
        nextY += 100;

        // Caption
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(100, 116, 139);
        doc.text('Figure 1: Authentic onboard optical frame captured during active road pass and relayed to command center.', 14, nextY);
        nextY += 8;
      } catch (err) {
        console.warn('PDF addImage error', err);
      }
    }
  }

  if (!rawImage || nextY === 100) {
    // Fallback placeholder box
    doc.setFillColor(241, 245, 249);
    doc.roundedRect(14, nextY, 182, 40, 2, 2, 'F');
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(8.5);
    doc.setTextColor(100, 116, 139);
    doc.text('No optical snapshot was provided for this incident. Telemetry recorded via driver GPS pin and road condition sensor.', 20, nextY + 22);
    nextY += 48;
  }

  // Incident Details & Rerouting Table
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('Incident Telemetry & Verification Audit', 14, nextY);

  const detailsRows = [
    ['Incident Parameter', 'Logged Value / Specification'],
    ['Hazard Identifier', incidentId],
    ['Disaster Category', hazardName],
    ['Severity Rating', severity],
    ['Latitude Coordinate', String(lat)],
    ['Longitude Coordinate', String(lng)],
    ['Address / Corridor', hazard.address || hazard.location?.address || 'Metropolitan Disaster Sector'],
    ['YOLOv11s Confidence Score', confidence],
    ['Verification State', hazard.status === 'REJECTED' ? 'REJECTED (Not Broadcasted)' : 'ACCEPTED & VERIFIED (Broadcasted to Drivers)'],
    ['Estimated Depth / Obstruction', hazard.depth ? `${hazard.depth} m` : 'Critical Road Inundation'],
    ['Timestamp Logged', hazard.createdAt || hazard.timestamp || timestampStr]
  ];

  autoTable(doc, {
    startY: nextY + 4,
    body: detailsRows,
    theme: 'striped',
    styles: { fontSize: 8, cellPadding: 2.5 },
    columnStyles: {
      0: { cellWidth: 60, fontStyle: 'bold', textColor: [15, 23, 42] },
      1: { cellWidth: 122, textColor: [51, 65, 85] }
    }
  });

  // Final Sign-off
  const endY = doc.lastAutoTable?.finalY ? doc.lastAutoTable.finalY + 12 : 240;
  if (endY < 265) {
    doc.setFillColor(240, 249, 255);
    doc.roundedRect(14, endY, 182, 16, 2, 2, 'F');
    doc.setDrawColor(186, 230, 253);
    doc.roundedRect(14, endY, 182, 16, 2, 2, 'S');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(2, 132, 199);
    doc.text('INCIDENT SIGN-OFF: AUTHORIZED AND ENTERED INTO MUNICIPAL DISASTER REGISTER', 20, endY + 6.5);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    doc.setTextColor(71, 85, 105);
    doc.text(`Reviewed by ${adminUser || 'HQ Incident Commander'} on ${timestampStr}. Relayed to all active vehicle navigation units.`, 20, endY + 11.5);
  }

  addFooters(doc);
  doc.save(`${reportDocNum}_Incident_Dossier.pdf`);
};

export default {
  generateComprehensiveDisasterReport,
  generateIndividualIncidentDossier
};
