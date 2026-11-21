const itemIds = new Intl.Collator("en", { numeric: true });

export const itemKind = (item) => typeof item === "string" ? item : item?.kind;
export const isSpoiled = (item, freshness) => Number.isFinite(item?.fresh) && item.fresh < (freshness?.spoiled_below ?? 30);
export const freshnessTone = (item, freshness) => isSpoiled(item, freshness) ? "spoiled" : item.fresh < 60 ? "soon" : "fresh";

export function reservedIdSet(snapshot) {
  return new Set((snapshot.customers ?? []).flatMap((customer) => Array.isArray(customer.reserved) ? customer.reserved : []));
}

export function availableItems(stock, reservedIds, freshness) {
  return stock.filter((item) => !reservedIds.has(item.id) && !isSpoiled(item, freshness));
}

export function groupItemsByKind(items, freshness) {
  const groups = Object.create(null);
  for (const item of items) {
    const group = groups[item.kind] ??= { fresh_count: 0, spoiled_count: 0, min_fresh: Infinity, avg_fresh: 0, items_sorted: [] };
    if (isSpoiled(item, freshness)) group.spoiled_count++;
    else group.fresh_count++;
    group.items_sorted.push(item);
    group.min_fresh = Math.min(group.min_fresh, item.fresh);
    group.avg_fresh += item.fresh;
  }
  for (const group of Object.values(groups)) {
    group.avg_fresh /= group.items_sorted.length;
    group.items_sorted.sort((a, b) => itemIds.compare(a.id, b.id));
  }
  return groups;
}

export function countKinds(items) {
  const counts = Object.create(null);
  for (const item of items) {
    const kind = itemKind(item);
    if (kind) counts[kind] = (counts[kind] ?? 0) + 1;
  }
  return counts;
}

export function availableCounts(snapshot, freshness) {
  const stock = snapshot.stock ?? {};
  if (Array.isArray(stock)) return countKinds(availableItems(stock, reservedIdSet(snapshot), freshness));
  const counts = { ...stock };
  for (const customer of snapshot.customers ?? []) {
    if (Array.isArray(customer.reserved)) continue;
    for (const [kind, amount] of Object.entries(customer.reserved ?? {})) counts[kind] = (counts[kind] ?? 0) - amount;
  }
  return counts;
}

export function groupedInventory(items, reservedIds, freshness) {
  const groups = groupItemsByKind(items, freshness);
  const available = countKinds(availableItems(items, reservedIds, freshness));
  return Object.fromEntries(Object.entries(groups).map(([kind, group]) => {
    const freshItems = group.items_sorted.filter((item) => !isSpoiled(item, freshness));
    return [kind, {
      count: available[kind] ?? 0,
      held: group.items_sorted.filter((item) => reservedIds.has(item.id)).length,
      spoiled: group.spoiled_count,
      min: freshItems[0] ? Math.min(...freshItems.map((item) => item.fresh)) : null,
      average: freshItems[0] ? freshItems.reduce((sum, item) => sum + item.fresh, 0) / freshItems.length : null,
    }];
  }));
}

export function receivedInventory(data) {
  const inventory = data?.inventory;
  if (Array.isArray(inventory)) return inventory;
  return inventory?.items ?? data?.stock;
}

export function inventoryHasItems(stock) {
  return Array.isArray(stock) ? stock.length > 0 : Object.values(stock ?? {}).some((amount) => amount > 0);
}

export function uiConfig(config) {
  const tuning = config.tuning ?? config;
  return { ...tuning, freshness: config.freshness ?? tuning.freshness };
}
