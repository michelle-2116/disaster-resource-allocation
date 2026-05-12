export function getNeedTypeLabel(type) {
  const map = {
    send_food: 'Food',
    send_meds: 'Medicine',
    send_water: 'Water',
    send_rescue_team: 'Rescue',
    reserve_resource: 'Resource'
  };
  return map[type] || 'Resource';
}

export function getNeedTypeColor(type) {
  const map = {
    send_food: 'text-accent-amber',
    send_meds: 'text-accent-red',
    send_water: 'text-accent-blue',
    send_rescue_team: 'text-accent-red',
    reserve_resource: 'text-gray-500'
  };
  return map[type] || 'text-gray-500';
}

export function filterPublicCards(cards) {
  return cards.filter(c => c.show_pd === true && c.fulfilled === false);
}

export function filterPendingCards(cards) {
  return cards.filter(c => c.pending_approval === true && c.show_pd === false && c.fulfilled === false);
}

export function groupCardsByIncident(cards, incidents) {
  const map = new Map();
  cards.forEach(card => {
    if (!map.has(card.incident_id)) {
      const incident = incidents.find(i => i.id === card.incident_id);
      map.set(card.incident_id, { incident, cards: [] });
    }
    map.get(card.incident_id).cards.push(card);
  });
  return map;
}

export function isCardClaimed(card) {
  return card.done_by !== null && card.fulfilled === false;
}

export function isCardOpen(card) {
  return card.done_by === null && card.fulfilled === false && card.show_pd === true;
}
