export const INCIDENTS = [
  {
    id: "inc_001",
    name: "Kerala Flood",
    location: "Alappuzha & Kuttanad",
    state: "Kerala",
    type: "Flood",
    severity: "critical",
    reported_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    affected_population: 15000,
    status: "active"
  },
  {
    id: "inc_002",
    name: "Odisha Cyclone",
    location: "Puri & Khordha",
    state: "Odisha",
    type: "Cyclone",
    severity: "high",
    reported_at: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
    affected_population: 25000,
    status: "active"
  },
  {
    id: "inc_003",
    name: "Nagpur Heatwave",
    location: "Nagpur City Wards 4-8",
    state: "Maharashtra",
    type: "Heatwave",
    severity: "high",
    reported_at: new Date(Date.now() - 144 * 60 * 60 * 1000).toISOString(),
    affected_population: 40000,
    status: "active"
  }
];
