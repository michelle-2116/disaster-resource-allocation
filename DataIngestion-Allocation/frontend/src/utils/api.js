export function updateCardInList(cards, updatedCard) {
  return cards.map(card => card.id === updatedCard.id ? updatedCard : card);
}
