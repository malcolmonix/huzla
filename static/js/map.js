let map;
let markers = [];

function initMap(elementId, center = [0, 0], zoom = 13) {
    map = L.map(elementId).setView(center, zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

function addMarker(lat, lng, title) {
    const marker = L.marker([lat, lng])
        .bindPopup(title)
        .addTo(map);
    markers.push(marker);
    return marker;
}

// Initialize map for service list
if (document.getElementById('map')) {
    navigator.geolocation.getCurrentPosition(function(position) {
        initMap('map', [position.coords.latitude, position.coords.longitude]);
        
        // Fetch and display services
        fetch('/api/services')
            .then(response => response.json())
            .then(services => {
                services.forEach(service => {
                    addMarker(service.lat, service.lng, 
                        `<strong>${service.title}</strong><br>
                        Provider: ${service.provider}<br>
                        Rate: $${service.rate}`);
                });
            });
    });
}

// Initialize map for service detail
if (document.getElementById('provider-map')) {
    initMap('provider-map', [providerLocation.lat, providerLocation.lng]);
    addMarker(providerLocation.lat, providerLocation.lng, 'Service Provider Location');
}
