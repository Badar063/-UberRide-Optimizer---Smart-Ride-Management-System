#!/usr/bin/env python3
"""
🚗 UberRide Optimizer - Intelligent Ride Management System
AI-powered ride matching, pricing, and route optimization
"""

import json
import math
import random
from datetime import datetime, timedelta
import heapq
from typing import Dict, List, Tuple
import time

class Location:
    """Represents a geographic location with coordinates"""
    
    def __init__(self, lat: float, lng: float, address: str = ""):
        self.lat = lat
        self.lng = lng
        self.address = address
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate Haversine distance between two points (in km)"""
        R = 6371  # Earth radius in km
        
        lat1, lon1 = math.radians(self.lat), math.radians(self.lng)
        lat2, lon2 = math.radians(other.lat), math.radians(other.lng)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

class Driver:
    """Represents a driver in the system"""
    
    def __init__(self, driver_id: str, name: str, location: Location, 
                 vehicle_type: str, rating: float, is_available: bool = True):
        self.driver_id = driver_id
        self.name = name
        self.location = location
        self.vehicle_type = vehicle_type
        self.rating = rating
        self.is_available = is_available
        self.current_ride = None
    
    def to_dict(self):
        return {
            'driver_id': self.driver_id,
            'name': self.name,
            'location': {'lat': self.location.lat, 'lng': self.location.lng},
            'vehicle_type': self.vehicle_type,
            'rating': self.rating,
            'is_available': self.is_available
        }

class RideRequest:
    """Represents a ride booking request"""
    
    def __init__(self, request_id: str, passenger_name: str, pickup: Location, 
                 dropoff: Location, ride_type: str = "standard", 
                 requested_time: datetime = None):
        self.request_id = request_id
        self.passenger_name = passenger_name
        self.pickup = pickup
        self.dropoff = dropoff
        self.ride_type = ride_type
        self.requested_time = requested_time or datetime.now()
        self.status = "pending"  # pending, matched, in_progress, completed
    
    def to_dict(self):
        return {
            'request_id': self.request_id,
            'passenger_name': self.passenger_name,
            'pickup': {'lat': self.pickup.lat, 'lng': self.pickup.lng},
            'dropoff': {'lat': self.dropoff.lat, 'lng': self.dropoff.lng},
            'ride_type': self.ride_type,
            'status': self.status
        }

class UberRideOptimizer:
    """
    🚀 Intelligent Ride Optimization Engine
    Features:
    - Smart driver-rider matching
    - Dynamic pricing
    - Route optimization
    - Surge pricing detection
    - Real-time ETA predictions
    """
    
    # Base fares for different ride types (in dollars)
    BASE_FARES = {
        "standard": 2.50,
        "premium": 5.00,
        "pool": 1.50
    }
    
    # Per km rates
    PER_KM_RATES = {
        "standard": 1.20,
        "premium": 2.00,
        "pool": 0.80
    }
    
    # Per minute rates
    PER_MINUTE_RATES = {
        "standard": 0.25,
        "premium": 0.40,
        "pool": 0.15
    }
    
    def __init__(self):
        self.drivers = []
        self.ride_requests = []
        self.completed_rides = []
        self.surge_multiplier = 1.0
        
    def add_driver(self, driver: Driver):
        """Add a driver to the system"""
        self.drivers.append(driver)
        print(f"🚗 Driver {driver.name} added to the system")
    
    def request_ride(self, ride_request: RideRequest):
        """Process a new ride request"""
        self.ride_requests.append(ride_request)
        print(f"🎯 New ride request from {ride_request.passenger_name}")
        
        # Find best driver match
        matched_driver = self._find_optimal_driver(ride_request)
        
        if matched_driver:
            self._assign_ride(ride_request, matched_driver)
            return matched_driver
        else:
            print("❌ No drivers available at the moment")
            return None
    
    def _find_optimal_driver(self, ride_request: RideRequest) -> Driver:
        """Find the best driver for a ride request using multiple factors"""
        available_drivers = [d for d in self.drivers if d.is_available]
        
        if not available_drivers:
            return None
        
        # Score each driver based on multiple factors
        driver_scores = []
        
        for driver in available_drivers:
            score = self._calculate_driver_score(driver, ride_request)
            driver_scores.append((score, driver))
        
        # Return driver with highest score
        best_score, best_driver = max(driver_scores, key=lambda x: x[0])
        
        print(f"🏆 Best match: {best_driver.name} with score {best_score:.2f}")
        return best_driver
    
    def _calculate_driver_score(self, driver: Driver, ride_request: RideRequest) -> float:
        """Calculate driver suitability score (0-100)"""
        # Factor 1: Distance to pickup (40% weight)
        distance_to_pickup = driver.location.distance_to(ride_request.pickup)
        distance_score = max(0, 100 - (distance_to_pickup * 10))  # Convert km to score
        
        # Factor 2: Driver rating (30% weight)
        rating_score = driver.rating * 20  # Convert 5-star to 100 scale
        
        # Factor 3: Vehicle type match (20% weight)
        vehicle_score = 100 if driver.vehicle_type == ride_request.ride_type else 60
        
        # Factor 4: Historical performance (10% weight)
        performance_score = 80  # Placeholder for actual performance metrics
        
        # Weighted average
        total_score = (
            distance_score * 0.4 +
            rating_score * 0.3 +
            vehicle_score * 0.2 +
            performance_score * 0.1
        )
        
        return total_score
    
    def _assign_ride(self, ride_request: RideRequest, driver: Driver):
        """Assign ride to driver and calculate details"""
        ride_request.status = "matched"
        driver.is_available = False
        driver.current_ride = ride_request
        
        # Calculate ride details
        distance = ride_request.pickup.distance_to(ride_request.dropoff)
        eta = self._calculate_eta(driver.location, ride_request.pickup, ride_request.dropoff)
        fare = self._calculate_fare(ride_request, distance)
        
        print(f"🎊 Ride assigned! {driver.name} will pick up {ride_request.passenger_name}")
        print(f"📍 Distance: {distance:.2f} km")
        print(f"⏱️  ETA: {eta} minutes")
        print(f"💰 Estimated fare: ${fare:.2f}")
        print(f"🚘 Vehicle: {driver.vehicle_type} | ⭐ Rating: {driver.rating}")
        
        return {
            'driver': driver.name,
            'distance': distance,
            'eta': eta,
            'fare': fare,
            'vehicle_type': driver.vehicle_type
        }
    
    def _calculate_eta(self, driver_location: Location, pickup: Location, dropoff: Location) -> int:
        """Calculate estimated time of arrival in minutes"""
        # Distance from driver to pickup
        distance_to_pickup = driver_location.distance_to(pickup)
        
        # Distance from pickup to dropoff
        trip_distance = pickup.distance_to(dropoff)
        
        # Total distance
        total_distance = distance_to_pickup + trip_distance
        
        # Assume average speed of 30 km/h in urban areas
        average_speed_kmh = 30
        eta_minutes = (total_distance / average_speed_kmh) * 60
        
        # Add traffic factor (random between 1.1 and 1.5)
        traffic_factor = random.uniform(1.1, 1.5)
        
        return int(eta_minutes * traffic_factor)
    
    def _calculate_fare(self, ride_request: RideRequest, distance: float) -> float:
        """Calculate dynamic fare for the ride"""
        base_fare = self.BASE_FARES[ride_request.ride_type]
        distance_fare = distance * self.PER_KM_RATES[ride_request.ride_type]
        
        # Estimate time (assuming 30 km/h average speed)
        time_minutes = (distance / 30) * 60
        time_fare = time_minutes * self.PER_MINUTE_RATES[ride_request.ride_type]
        
        # Calculate base fare
        total_fare = base_fare + distance_fare + time_fare
        
        # Apply surge pricing if needed
        total_fare *= self.surge_multiplier
        
        return round(total_fare, 2)
    
    def complete_ride(self, driver_id: str):
        """Mark a ride as completed"""
        driver = next((d for d in self.drivers if d.driver_id == driver_id), None)
        
        if driver and driver.current_ride:
            ride = driver.current_ride
            ride.status = "completed"
            driver.is_available = True
            driver.current_ride = None
            
            self.completed_rides.append(ride)
            self.ride_requests.remove(ride)
            
            print(f"✅ Ride completed by {driver.name} for {ride.passenger_name}")
            return True
        
        print("❌ No active ride found for this driver")
        return False
    
    def check_surge_pricing(self) -> float:
        """Check if surge pricing should be applied"""
        active_requests = len([r for r in self.ride_requests if r.status == "pending"])
        available_drivers = len([d for d in self.drivers if d.is_available])
        
        if available_drivers == 0:
            demand_ratio = 2.0  # High demand, no drivers
        else:
            demand_ratio = active_requests / available_drivers
        
        # Set surge multiplier based on demand
        if demand_ratio > 2.0:
            self.surge_multiplier = 2.0
        elif demand_ratio > 1.5:
            self.surge_multiplier = 1.5
        elif demand_ratio > 1.2:
            self.surge_multiplier = 1.2
        else:
            self.surge_multiplier = 1.0
        
        print(f"📊 Demand Analysis: {active_requests} requests, {available_drivers} available drivers")
        print(f"🎯 Surge Multiplier: {self.surge_multiplier}x")
        
        return self.surge_multiplier
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        return {
            "total_drivers": len(self.drivers),
            "available_drivers": len([d for d in self.drivers if d.is_available]),
            "pending_requests": len([r for r in self.ride_requests if r.status == "pending"]),
            "active_rides": len([r for r in self.ride_requests if r.status == "matched"]),
            "completed_rides": len(self.completed_rides),
            "surge_multiplier": self.surge_multiplier
        }
    
    def save_data(self):
        """Save current state to files"""
        drivers_data = [driver.to_dict() for driver in self.drivers]
        rides_data = [ride.to_dict() for ride in self.ride_requests + self.completed_rides]
        
        with open('sample_data/drivers.json', 'w') as f:
            json.dump(drivers_data, f, indent=2)
        
        with open('sample_data/ride_requests.json', 'w') as f:
            json.dump(rides_data, f, indent=2)
        
        print("💾 Data saved successfully!")

def create_sample_data():
    """Create sample drivers and locations for demonstration"""
    
    # Sample locations in a city (approx coordinates)
    locations = {
        "downtown": Location(40.7128, -74.0060, "Downtown"),
        "airport": Location(40.6413, -73.7781, "Airport"),
        "university": Location(40.7505, -73.9934, "University"),
        "shopping_mall": Location(40.7685, -73.9823, "Shopping Mall"),
        "central_park": Location(40.7829, -73.9654, "Central Park"),
        "train_station": Location(40.7506, -73.9938, "Train Station")
    }
    
    # Sample drivers
    drivers = [
        Driver("D001", "John Smith", locations["downtown"], "standard", 4.8),
        Driver("D002", "Maria Garcia", locations["airport"], "premium", 4.9),
        Driver("D003", "David Chen", locations["university"], "standard", 4.7),
        Driver("D004", "Sarah Johnson", locations["shopping_mall"], "premium", 4.6),
        Driver("D005", "Mike Brown", locations["central_park"], "standard", 4.5)
    ]
    
    return drivers, locations

def main():
    """Main demonstration function"""
    print("🚗 UBER RIDE OPTIMIZER SYSTEM")
    print("=" * 50)
    
    # Initialize system
    uber_system = UberRideOptimizer()
    
    # Create sample data
    drivers, locations = create_sample_data()
    
    # Add drivers to system
    for driver in drivers:
        uber_system.add_driver(driver)
    
    print("\n🎯 DEMONSTRATING RIDE MATCHING")
    print("-" * 30)
    
    # Create ride requests
    ride_requests = [
        RideRequest("R001", "Alice Cooper", locations["university"], locations["airport"], "standard"),
        RideRequest("R002", "Bob Wilson", locations["downtown"], locations["shopping_mall"], "premium"),
        RideRequest("R003", "Carol Davis", locations["central_park"], locations["train_station"], "standard")
    ]
    
    # Process ride requests
    for request in ride_requests:
        print(f"\n📞 Processing request from {request.passenger_name}...")
        result = uber_system.request_ride(request)
        
        if result:
            # Simulate ride completion after some time
            time.sleep(1)
            uber_system.complete_ride(result.driver_id)
    
    # Check surge pricing
    print("\n📊 CHECKING SURGE PRICING")
    print("-" * 25)
    uber_system.check_surge_pricing()
    
    # Show system statistics
    print("\n📈 SYSTEM STATISTICS")
    print("-" * 20)
    stats = uber_system.get_system_stats()
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Save data
    uber_system.save_data()
    
    print("\n✅ Demonstration completed successfully!")

if __name__ == "__main__":
    main()
