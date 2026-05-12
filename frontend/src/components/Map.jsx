import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;
const DisasterMap = ({ data }) => {
  const warehousePos = [12.9716, 77.5946]; // Bangalore Coordinates

  return (
    <MapContainer center={warehousePos} zoom={11} className="h-[600px] w-full rounded-lg">
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      
      {/* Warehouse */}
      <Marker position={warehousePos}>
        <Popup>Central Logistics Hub</Popup>
      </Marker>

      {/* Incidents */}
      {data.incidents?.map(inc => (
        <Circle 
          key={inc.id} 
          center={[inc.location_lat, inc.location_lng]} 
          radius={2000} 
          pathOptions={{ color: 'red', fillOpacity: 0.3 }}
        >
          <Popup><strong>{inc.title}</strong><br/>Severity: {inc.severity}</Popup>
        </Circle>
      ))}

      {/* Shelters */}
      {data.shelters?.map(s => (
        <Marker key={s.id} position={[s.lat, s.lng]}>
          <Popup>{s.name}</Popup>
        </Marker>
      ))}

      {/* Routes */}
      {data.dispatches?.map(d => (
        <Polyline 
          key={d.id} 
          positions={d.route_geometry.coordinates.map(c => [c[1], c[0]])} 
          color="blue" 
          weight={4}
        />
      ))}

      {/* Blocked Roads */}
      {data.blocked_roads?.map(b => (
        <Circle 
          key={b.id} 
          center={[b.lat, b.lng]} 
          radius={500} 
          pathOptions={{ color: 'black', fillColor: 'black' }}
        >
          <Popup>ROAD BLOCKED: {b.reason}</Popup>
        </Circle>
      ))}
    </MapContainer>
  );
};

export default DisasterMap;