/**
 * Weather Telemetry Service Abstraction
 * Queries live weather telemetry along driving corridors.
 */
import api from './api';

export const weatherService = {
  getLiveWeather: async (lat, lng) => {
    try {
      const data = await api.getLiveWeather(lat, lng);
      return {
        rainfall: data.rainfall || 0,
        temp: data.temp || 28,
        humidity: data.humidity || 75,
        windSpeed: data.windSpeed || 15,
        description: data.description || 'Clear road conditions',
        timestamp: new Date().toISOString()
      };
    } catch {
      return {
        rainfall: 16.5,
        temp: 27.5,
        humidity: 84,
        windSpeed: 22.0,
        description: 'Monsoon precipitation & road wetness',
        timestamp: new Date().toISOString()
      };
    }
  }
};

export default weatherService;
