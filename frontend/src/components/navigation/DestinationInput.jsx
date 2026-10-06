import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Search, X, Loader2, History, Clock } from 'lucide-react';
import mapboxService from '../../services/mapboxService';
import cacheService from '../../services/cacheService';

export const DestinationInput = ({ onSelectDestination, selectedDestination, currentLocation, disabled }) => {
  const [query, setQuery] = useState(selectedDestination?.name || '');
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [recentDestinations, setRecentDestinations] = useState([]);
  const debounceTimerRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    // Load recent destinations from memory cache
    setRecentDestinations(cacheService.getRecentDestinations());
  }, []);

  useEffect(() => {
    if (selectedDestination?.name && query !== selectedDestination.name) {
      setQuery(selectedDestination.name);
    }
  }, [selectedDestination]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsFocused(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (val.trim().length > 1) {
      setIsSearching(true);
      debounceTimerRef.current = setTimeout(async () => {
        const proximity = currentLocation ? [currentLocation.lng, currentLocation.lat] : null;
        const results = await mapboxService.searchDestinationV6(val, proximity);
        setSuggestions(results);
        setIsSearching(false);
      }, 250);
    } else {
      setSuggestions([]);
      setIsSearching(false);
    }
  };

  const handleSelect = (dest) => {
    setQuery(dest.name);
    setSuggestions([]);
    setIsFocused(false);

    // Save selected place into persistent memory cache
    const updatedMemory = cacheService.saveDestinationToMemory(dest);
    if (updatedMemory) setRecentDestinations(updatedMemory);

    if (onSelectDestination) {
      onSelectDestination({
        name: dest.name,
        full_address: dest.full_address || dest.name,
        lat: dest.lat,
        lng: dest.lng
      });
    }
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
  };

  const showRecent = isFocused && suggestions.length === 0 && recentDestinations.length > 0;

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', maxWidth: '440px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderRadius: '12px',
          padding: '10px 14px',
          boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.12), 0 2px 6px -1px rgba(15, 23, 42, 0.04)',
          border: '1px solid rgba(255, 255, 255, 0.7)'
        }}
      >
        <MapPin size={18} color="#0284c7" style={{ marginRight: '10px', flexShrink: 0 }} />
        <input
          type="text"
          value={query}
          onFocus={() => setIsFocused(true)}
          onChange={handleInputChange}
          placeholder="Enter Destination (Mapbox v6 Search)..."
          disabled={disabled}
          style={{
            border: 'none',
            outline: 'none',
            width: '100%',
            fontSize: '0.92rem',
            color: '#0f172a',
            fontWeight: 600,
            background: 'transparent'
          }}
        />
        {isSearching && (
          <Loader2 size={16} className="animate-spin" color="#0284c7" style={{ marginRight: '6px' }} />
        )}
        {query && !isSearching && (
          <button
            onClick={handleClear}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#94a3b8' }}
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Mapbox Geocoding v6 Suggestions */}
      {suggestions.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            background: '#ffffff',
            borderRadius: '10px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.15)',
            border: '1px solid #cbd5e1',
            zIndex: 1000,
            maxHeight: '260px',
            overflowY: 'auto'
          }}
        >
          {suggestions.map((item, idx) => (
            <div
              key={item.id || idx}
              onClick={() => handleSelect(item)}
              style={{
                padding: '10px 14px',
                fontSize: '0.84rem',
                color: '#1e293b',
                cursor: 'pointer',
                borderBottom: idx < suggestions.length - 1 ? '1px solid #f1f5f9' : 'none',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#ffffff')}
            >
              <Search size={15} color="#0284c7" style={{ marginTop: '2px', flexShrink: 0 }} />
              <div>
                <strong style={{ display: 'block', color: '#0f172a' }}>{item.name}</strong>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>{item.full_address}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Persistent Memory: Recent Destinations Dropdown */}
      {showRecent && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(16px)',
            borderRadius: '12px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.15)',
            border: '1px solid #cbd5e1',
            zIndex: 1000,
            maxHeight: '260px',
            overflowY: 'auto'
          }}
        >
          <div style={{ padding: '8px 14px', fontSize: '0.72rem', fontWeight: 800, color: '#0284c7', background: '#f0f9ff', borderBottom: '1px solid #e0f2fe', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <History size={13} />
            <span>RECENT DESTINATIONS (MEMORY CACHE)</span>
          </div>
          {recentDestinations.map((item, idx) => (
            <div
              key={idx}
              onClick={() => handleSelect(item)}
              style={{
                padding: '10px 14px',
                fontSize: '0.84rem',
                color: '#1e293b',
                cursor: 'pointer',
                borderBottom: idx < recentDestinations.length - 1 ? '1px solid #f1f5f9' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '10px'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f0f9ff')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Clock size={15} color="#64748b" style={{ flexShrink: 0 }} />
                <div>
                  <strong style={{ display: 'block', color: '#0f172a' }}>{item.name}</strong>
                  <span style={{ fontSize: '0.74rem', color: '#64748b' }}>{item.full_address}</span>
                </div>
              </div>
              <span style={{ fontSize: '0.68rem', color: '#0284c7', background: '#e0f2fe', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                1-CLICK
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DestinationInput;
