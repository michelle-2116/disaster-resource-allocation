import { Circle, MapContainer, Marker, Polyline, Popup, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

const marker = (className, label) =>
  L.divIcon({
    className: '',
    html: `<div class="${className}">${label}</div>`,
    iconSize: [46, 46],
    iconAnchor: [23, 23],
  });

const icons = {
  warehouse: marker('map-pin map-pin-warehouse', 'W'),
  shelter: marker('map-pin map-pin-shelter', 'S'),
  block: marker('map-pin map-pin-block', '!'),
};

const severityColor = {
  critical: '#dc2626',
  high: '#f97316',
  medium: '#facc15',
  low: '#38bdf8',
};

function DisasterMap({ data }) {
  const center = data.center ? [data.center.lat, data.center.lng] : [11.6854, 76.132];

  return (
    <MapContainer center={center} zoom={11} minZoom={9} className="h-full w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {data.incidents?.map((incident) => (
        <Circle
          key={incident.id}
          center={[incident.location_lat, incident.location_lng]}
          radius={incident.radius_meters ?? 2600}
          pathOptions={{
            color: severityColor[incident.severity] ?? '#ef4444',
            fillColor: severityColor[incident.severity] ?? '#ef4444',
            fillOpacity: 0.22,
            weight: 2,
          }}
        >
          <Popup>
            <strong>{incident.title}</strong>
            <br />
            {incident.type} | {incident.severity}
            <br />
            {incident.summary}
          </Popup>
        </Circle>
      ))}

      {data.dispatches?.map((dispatch) => {
        const positions = dispatch.route_geometry?.coordinates?.map((coord) => [coord[1], coord[0]]) ?? [];
        return (
          <Polyline
            key={dispatch.id}
            positions={positions}
            color={dispatch.rerouted ? '#a78bfa' : '#06b6d4'}
            weight={8}
            opacity={0.9}
            dashArray={dispatch.rerouted ? '14 10' : undefined}
          >
            <Popup>
              <strong>{dispatch.item_type} dispatch</strong>
              <br />
              {dispatch.warehouse_name} to {dispatch.shelter_name}
              <br />
              {(dispatch.distance / 1000).toFixed(1)} km | {Math.round(dispatch.estimated_time / 60)} min
              <br />
              {dispatch.rerouted ? 'Rerouted around a blocked road' : 'Best available path'}
            </Popup>
          </Polyline>
        );
      })}

      {data.suggested_routes?.map((route) => {
        const positions = route.route_geometry?.coordinates?.map((coord) => [coord[1], coord[0]]) ?? [];
        return (
          <Polyline
            key={route.id}
            positions={positions}
            color={route.rerouted ? '#f59e0b' : '#94a3b8'}
            weight={6}
            opacity={0.82}
            dashArray="8 10"
          >
            <Popup>
              <strong>Suggested best path</strong>
              <br />
              {route.item_type} from {route.warehouse_name}
              <br />
              to {route.shelter_name}
              <br />
              {(route.distance / 1000).toFixed(1)} km | {Math.round(route.estimated_time / 60)} min
            </Popup>
          </Polyline>
        );
      })}

      {data.warehouses?.map((warehouse) => (
        <Marker key={warehouse.id} position={[warehouse.lat, warehouse.lng]} icon={icons.warehouse}>
          <Popup>
            <strong>{warehouse.name}</strong>
            <br />
            {warehouse.access}
            <br />
            {warehouse.resources.map((resource) => `${resource.item_name}: ${resource.quantity}`).join(', ')}
          </Popup>
        </Marker>
      ))}

      {data.shelters?.map((shelter) => (
        <Marker key={shelter.id} position={[shelter.lat, shelter.lng]} icon={icons.shelter}>
          <Popup>
            <strong>{shelter.name}</strong>
            <br />
            Occupancy: {shelter.current_occupancy}/{shelter.capacity}
            <br />
            Risk: {shelter.risk}
          </Popup>
        </Marker>
      ))}

      {data.blocked_roads?.map((block) => (
        <Circle
          key={block.id}
          center={[block.lat, block.lng]}
          radius={block.radius_meters ?? 800}
          pathOptions={{ color: '#18181b', fillColor: '#f97316', fillOpacity: 0.38, weight: 5 }}
        >
          <Popup>
            <strong>Road blocked</strong>
            <br />
            {block.reason}
            <br />
            Source: {block.source}
          </Popup>
        </Circle>
      ))}

      {data.blocked_roads?.map((block) => (
        <Marker key={`${block.id}-marker`} position={[block.lat, block.lng]} icon={icons.block}>
          <Popup>{block.reason}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default DisasterMap;
