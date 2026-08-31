import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Search, Navigation, Stethoscope, ChevronDown, Loader2 } from 'lucide-react';
import api from '../services/api';

export interface LocationOption {
  display_name: string;
  lat: number;
  lng: number;
}

interface PractoSearchBarProps {
  onSearch: (params: { lat: number; lng: number; locationName: string; specialty: string }) => void;
  initialSpecialty?: string;
  className?: string;
}

export const PractoSearchBar: React.FC<PractoSearchBarProps> = ({
  onSearch,
  initialSpecialty = '',
  className = ''
}) => {
  const [locationQuery, setLocationQuery] = useState<string>('Indore, MP');
  const [selectedLocation, setSelectedLocation] = useState<LocationOption | null>({
    display_name: 'Indore, Madhya Pradesh, India',
    lat: 22.7533,
    lng: 75.8937
  });
  
  const [suggestions, setSuggestions] = useState<LocationOption[]>([]);
  const [isGeocoding, setIsGeocoding] = useState<boolean>(false);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [isDetectingGeo, setIsDetectingGeo] = useState<boolean>(false);

  const [specialties, setSpecialties] = useState<string[]>([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>(initialSpecialty);
  const [loadingSpecialties, setLoadingSpecialties] = useState<boolean>(true);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch specialties on mount
  useEffect(() => {
    fetchSpecialties();
  }, []);

  // Handle outside click to close location dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSpecialties = async () => {
    try {
      const res = await api.get('/doctors/specialties');
      setSpecialties(res.data || []);
    } catch (err) {
      console.error('Failed to load specialties:', err);
      setSpecialties(['Cardiology', 'Dermatology', 'General Medicine', 'Neurology', 'Orthopedics', 'Pediatrics']);
    } finally {
      setLoadingSpecialties(false);
    }
  };

  // Debounced location geocoding (450ms)
  const handleLocationInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setLocationQuery(val);
    setSelectedLocation(null);
    setErrorMessage(null);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!val || val.trim().length < 3) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    setIsGeocoding(true);
    debounceTimerRef.current = setTimeout(async () => {
      try {
        const res = await api.get(`/location/geocode?q=${encodeURIComponent(val)}`);
        const results = res.data?.results || [];
        if (results.length > 0) {
          setSuggestions(results);
          setShowDropdown(true);
        } else {
          // Direct client fallback to OpenStreetMap Nominatim API if backend endpoint returns empty
          const fallbackRes = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val)}&format=json&limit=5`,
            { headers: { 'Accept': 'application/json' } }
          );
          if (fallbackRes.ok) {
            const raw = await fallbackRes.json();
            const mapped = raw.map((item: any) => ({
              display_name: item.display_name,
              lat: parseFloat(item.lat),
              lng: parseFloat(item.lon)
            }));
            setSuggestions(mapped);
            setShowDropdown(mapped.length > 0);
          }
        }
      } catch (err) {
        console.warn('Geocode search backend failed, trying direct OSM Nominatim fallback:', err);
        try {
          const fallbackRes = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val)}&format=json&limit=5`,
            { headers: { 'Accept': 'application/json' } }
          );
          if (fallbackRes.ok) {
            const raw = await fallbackRes.json();
            const mapped = raw.map((item: any) => ({
              display_name: item.display_name,
              lat: parseFloat(item.lat),
              lng: parseFloat(item.lon)
            }));
            setSuggestions(mapped);
            setShowDropdown(mapped.length > 0);
          }
        } catch (fallbackErr) {
          console.error('Direct OSM fallback also failed:', fallbackErr);
          setSuggestions([]);
        }
      } finally {
        setIsGeocoding(false);
      }
    }, 450);
  };

  const handleSelectSuggestion = (opt: LocationOption) => {
    setSelectedLocation(opt);
    setLocationQuery(opt.display_name.split(',')[0] + ', ' + (opt.display_name.split(',')[1] || ''));
    setShowDropdown(false);
    setSuggestions([]);
    setErrorMessage(null);
  };

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }

    setIsDetectingGeo(true);
    setErrorMessage(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords: LocationOption = {
          display_name: 'Current Location',
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        };
        setSelectedLocation(coords);
        setLocationQuery('Current Location');
        setIsDetectingGeo(false);
      },
      (error) => {
        console.warn('Browser geolocation error:', error.message);
        setIsDetectingGeo(false);
        setErrorMessage('Location permission denied or unavailable. Please type your city/area in the location box.');
      },
      { timeout: 8000, maximumAge: 60000 }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let loc = selectedLocation;

    if (!loc && locationQuery.trim()) {
      // Attempt direct client-side geocode if user pressed Enter without picking dropdown
      try {
        const fallbackRes = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(locationQuery)}&format=json&limit=1`,
          { headers: { 'Accept': 'application/json' } }
        );
        if (fallbackRes.ok) {
          const raw = await fallbackRes.json();
          if (raw.length > 0) {
            loc = {
              display_name: raw[0].display_name,
              lat: parseFloat(raw[0].lat),
              lng: parseFloat(raw[0].lon)
            };
            setSelectedLocation(loc);
          }
        }
      } catch (err) {
        console.warn('Direct submit geocode failed:', err);
      }
    }

    // Default fallback to Indore coordinates if geocoding yields no specific match
    if (!loc) {
      loc = {
        display_name: locationQuery || 'Indore, MP',
        lat: 22.7533,
        lng: 75.8937
      };
      setSelectedLocation(loc);
    }

    setErrorMessage(null);
    onSearch({
      lat: loc.lat,
      lng: loc.lng,
      locationName: locationQuery || 'Indore, MP',
      specialty: selectedSpecialty
    });
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <form
        onSubmit={handleSubmit}
        className="bg-white p-2.5 sm:p-3 rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-lg flex flex-col md:flex-row items-stretch gap-2.5"
      >
        {/* Location Input (Side 1) */}
        <div ref={dropdownRef} className="relative flex-1 flex items-center bg-slate-50 hover:bg-slate-100/80 rounded-xl sm:rounded-2xl px-3 py-2.5 transition-colors border border-slate-200/60">
          <MapPin className="w-5 h-5 text-medical-600 flex-shrink-0 mr-2" />
          <input
            type="text"
            value={locationQuery}
            onChange={handleLocationInputChange}
            onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
            placeholder="City, area, or location..."
            className="w-full bg-transparent text-xs sm:text-sm font-semibold text-slate-800 focus:outline-none placeholder:text-slate-400"
          />

          {isGeocoding && <Loader2 className="w-4 h-4 text-slate-400 animate-spin mr-2" />}

          {/* Use Current Location Icon Button */}
          <button
            type="button"
            onClick={handleUseCurrentLocation}
            title="Use Current Location"
            disabled={isDetectingGeo}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 font-bold text-xs transition-colors flex-shrink-0 border border-medical-200/60 ml-1"
          >
            {isDetectingGeo ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-medical-600" />
            ) : (
              <Navigation className="w-3.5 h-3.5 text-medical-600 fill-medical-600" />
            )}
            <span className="hidden sm:inline">GPS</span>
          </button>

          {/* Location Autocomplete Dropdown */}
          {showDropdown && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 max-h-60 overflow-y-auto py-1">
              {suggestions.map((opt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectSuggestion(opt)}
                  className="w-full text-left px-4 py-2.5 hover:bg-medical-50 transition-colors flex items-start gap-2.5 border-b border-slate-100 last:border-0"
                >
                  <MapPin className="w-4 h-4 text-medical-500 flex-shrink-0 mt-0.5" />
                  <span className="text-xs font-medium text-slate-700 line-clamp-2 leading-relaxed">
                    {opt.display_name}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Specialty Input (Side 2) */}
        <div className="relative flex-1 flex items-center bg-slate-50 hover:bg-slate-100/80 rounded-xl sm:rounded-2xl px-3 py-2.5 transition-colors border border-slate-200/60">
          <Stethoscope className="w-5 h-5 text-tealmed-600 flex-shrink-0 mr-2" />
          <select
            value={selectedSpecialty}
            onChange={(e) => setSelectedSpecialty(e.target.value)}
            disabled={loadingSpecialties}
            className="w-full bg-transparent text-xs sm:text-sm font-semibold text-slate-800 focus:outline-none cursor-pointer appearance-none pr-6"
          >
            <option value="">All Specialties / Specializations</option>
            {specialties.map((spec) => (
              <option key={spec} value={spec}>
                {spec}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 pointer-events-none" />
        </div>

        {/* Submit Search Button */}
        <button
          type="submit"
          className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-medical-600 to-tealmed-600 hover:from-medical-700 hover:to-tealmed-700 text-white font-bold text-xs sm:text-sm rounded-xl sm:rounded-2xl shadow-md shadow-medical-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex-shrink-0"
        >
          <Search className="w-4 h-4" />
          <span>Search Doctors</span>
        </button>
      </form>

      {/* Error / Helper Banner */}
      {errorMessage && (
        <div className="bg-amber-50 border border-amber-200/80 rounded-xl p-3 text-xs font-medium text-amber-800 flex items-center justify-between">
          <span>{errorMessage}</span>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-amber-600 hover:text-amber-900 font-bold ml-2"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
};
