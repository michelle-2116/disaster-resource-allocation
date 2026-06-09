import React, { useMemo } from 'react';
import { Circle, MapContainer, Marker, Polyline, Popup, TileLayer, useMapEvents } from 'react-leaflet';
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
  draftBlock: marker('map-pin map-pin-draft-block', '+'),
  detour: marker('map-pin map-pin-detour', 'D'),
};

const severityColor = {
  critical: '#dc2626',
  high: '#f97316',
  medium: '#facc15',
  low: '#38bdf8',
};

function MapClickHandler({ onBlockPointSelected }) {
  useMapEvents({
    click(event) {
      onBlockPointSelected?.({
        lat: event.latlng.lat.toFixed(5),
        lng: event.latlng.lng.toFixed(5),
      });
    },
  });
  return null;
}

const DisasterMap = React.memo(function DisasterMap({ data, blockDraft, onBlockPointSelected }) {
  const center = useMemo(() => {
    return data.center ? [data.center.lat, data.center.lng] : [11.6854, 76.132];
  }, [data.center]);

  const draftPosition = useMemo(() => {
    const draftLat = Number(blockDraft?.lat);
    const draftLng = Number(blockDraft?.lng);
    if (Number.isFinite(draftLat) && Number.isFinite(draftLng)) {
      return [draftLat, draftLng];
    }
    return null;
  }, [blockDraft?.lat, blockDraft?.lng]);

  const draftRadius = Number(blockDraft?.radius_meters) || 800;

  return (
    <MapContainer center={center} zoom={11} minZoom={9} className="h-full w-full">
      <MapClickHandler onBlockPointSelected={onBlockPointSelected} />
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
          <RoutePolyline
            key={dispatch.id}
            route={dispatch}
            positions={positions}
            color={dispatch.rerouted ? '#c084fc' : '#06b6d4'}
            weight={dispatch.rerouted ? 10 : 8}
            dashArray={dispatch.rerouted ? '16 8' : undefined}
            title={`${dispatch.item_type} dispatch`}
          />
        );
      })}

      {data.dispatches?.filter((dispatch) => dispatch.detour_waypoint).map((dispatch) => (
        <Marker
          key={`${dispatch.id}-detour`}
          position={[dispatch.detour_waypoint.lat, dispatch.detour_waypoint.lng]}
          icon={icons.detour}
        >
          <Popup>
            <strong>Detour waypoint</strong>
            <br />
            Route bends here to avoid: {dispatch.blocked_by_reason ?? dispatch.blocked_by}
          </Popup>
        </Marker>
      ))}

      {data.suggested_routes?.map((route) => {
        const positions = route.route_geometry?.coordinates?.map((coord) => [coord[1], coord[0]]) ?? [];
        return (
          <RoutePolyline
            key={route.id}
            route={route}
            positions={positions}
            color={route.rerouted ? '#f59e0b' : '#94a3b8'}
            weight={route.rerouted ? 9 : 6}
            dashArray={route.rerouted ? '18 8' : '8 10'}
            title="Suggested updated path"
          />
        );
      })}

      {data.suggested_routes?.filter((route) => route.detour_waypoint).map((route) => (
        <Marker
          key={`${route.id}-detour`}
          position={[route.detour_waypoint.lat, route.detour_waypoint.lng]}
          icon={icons.detour}
        >
          <Popup>
            <strong>Suggested detour waypoint</strong>
            <br />
            Avoids: {route.blocked_by_reason ?? route.blocked_by}
          </Popup>
        </Marker>
      ))}

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
            Radius: {Math.round(block.radius_meters ?? 800)} m
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

      {draftPosition && (
        <>
          <Circle
            center={draftPosition}
            radius={draftRadius}
            pathOptions={{ color: '#facc15', fillColor: '#facc15', fillOpacity: 0.16, weight: 3, dashArray: '8 8' }}
          />
          <Marker position={draftPosition} icon={icons.draftBlock}>
            <Popup>
              <strong>New road block location</strong>
              <br />
              Submit the form to mark this block and recalculate routes.
            </Popup>
          </Marker>
        </>
      )}
    </MapContainer>
  );
}, (prevProps, nextProps) => {
  // custom comparison to skip rendering if coordinates and data are same
  const dataChanged = prevProps.data !== nextProps.data;
  const draftLatChanged = prevProps.blockDraft?.lat !== nextProps.blockDraft?.lat;
  const draftLngChanged = prevProps.blockDraft?.lng !== nextProps.blockDraft?.lng;
  const draftRadiusChanged = prevProps.blockDraft?.radius_meters !== nextProps.blockDraft?.radius_meters;
  return !dataChanged && !draftLatChanged && !draftLngChanged && !draftRadiusChanged;
});

const RoutePolyline = React.memo(function RoutePolyline({ route, positions, color, weight, dashArray, title }) {
  if (!positions.length) return null;

  return (
    <>
      <Polyline
        positions={positions}
        color="#0f172a"
        weight={weight + 5}
        opacity={0.75}
        dashArray={dashArray}
      />
      <Polyline
        positions={positions}
        color={color}
        weight={weight}
        opacity={0.96}
        dashArray={dashArray}
      >
        <Popup>
          <strong>{title}</strong>
          <br />
          {route.item_type} from {route.warehouse_name}
          <br />
          to {route.shelter_name}
          <br />
          {(route.distance / 1000).toFixed(1)} km | {Math.round(route.estimated_time / 60)} min
          <br />
          {route.rerouted ? 'Updated route avoids blocked road' : 'Current optimized route'}
          <br />
          {route.route_explanation}
        </Popup>
      </Polyline>
    </>
  );
}, (prevProps, nextProps) => {
  // compare array contents
  const prevPos = prevProps.positions;
  const nextPos = nextProps.positions;
  if (prevPos.length !== nextPos.length) return false;
  for (let i = 0; i < prevPos.length; i++) {
    if (prevPos[i][0] !== nextPos[i][0] || prevPos[i][1] !== nextPos[i][1]) {
      return false;
    }
  }
  return (
    prevProps.color === nextProps.color &&
    prevProps.weight === nextProps.weight &&
    prevProps.dashArray === nextProps.dashArray &&
    prevProps.title === nextProps.title &&
    prevProps.route.status === nextProps.route.status
  );
});

export default DisasterMap;
