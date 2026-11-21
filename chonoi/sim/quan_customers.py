from ..ids import sort_by_id
from ..errors import BadInput


class CustomerManager:
    def __init__(self, tuning, scenario, streams, ids, stock):
        self.tuning = tuning
        self.menu = tuning["menu"]
        quan = tuning["quan"]
        self.stock = stock
        self.rng = streams
        self.ids = ids
        self.patience_ticks = int(round(quan["patience_s"] * 60))
        self.interval_ticks = int(round(quan["customer_interval_s"] * 60))
        self.first_customer_tick = int(quan["first_customer_tick"])
        self.customers = [dict(c, reserved=dict(c.get("reserved", {}))) for c in scenario.get("customers", [])]
        for customer in self.customers:
            ids.reserve(customer["id"])
            if "patience_ticks" not in customer:
                customer["patience_ticks"] = self.patience_ticks
            if "state" not in customer:
                customer["state"] = "waiting"
            if "dish" not in customer:
                customer["dish"] = None
            if customer.get("state") == "waiting" and customer["dish"] and not customer["reserved"]:
                customer["reserved"] = dict(self.menu[customer["dish"]]["recipe"])
        reserved_totals = {}
        for customer in self.customers:
            for kind, count in customer.get("reserved", {}).items():
                reserved_totals[kind] = reserved_totals.get(kind, 0) + count
        for kind, count in reserved_totals.items():
            if count > stock.get(kind, 0):
                raise BadInput(f"khách giữ chỗ vượt số nguyên liệu trong kho: {kind}")
        self.random_customers = scenario.get("random_customers", True)
        self.elapsed_ticks = 0
        self.next_customer_tick = self.first_customer_tick

    def available_stock(self):
        available = dict(self.stock)
        for customer in self.customers:
            if customer.get("state") not in ("left", "eating", "paid"):
                for kind, count in customer.get("reserved", {}).items():
                    available[kind] = available.get(kind, 0) - count
        return available

    def cookable_dishes(self):
        available = self.available_stock()
        cookable = []
        for dish, spec in sorted(self.menu.items()):
            if all(available.get(kind, 0) >= count for kind, count in spec["recipe"].items()):
                cookable.append(dish)
        return cookable

    def reserve(self, dish):
        recipe = self.menu[dish]["recipe"]
        reserved = {}
        for kind, count in sorted(recipe.items()):
            available = self.available_stock()[kind] if kind in self.available_stock() else 0
            if available < count:
                return None
            reserved[kind] = count
        return reserved

    def step(self, tables):
        events = []
        self.elapsed_ticks += 1

        left = []
        for customer in sort_by_id(self.customers):
            if customer.get("state") == "waiting":
                customer["patience_ticks"] = max(0, customer["patience_ticks"] - 1)
                if customer["patience_ticks"] == 0:
                    left.append(customer)

        for customer in left:
            self.customers.remove(customer)
            tuning = self.tuning["quan"]
            self._reputation = getattr(self, "_reputation", tuning["reputation_initial"])
            events.append(("customer_left", {
                "customer_id": customer["id"],
                "table_id": customer["table_id"],
                "reserved": dict(customer.get("reserved", {})),
            }))

        if self.random_customers and self.elapsed_ticks == self.next_customer_tick:
            event = self._spawn_customer(tables)
            if event:
                events.append(event)
            self.next_customer_tick += self.interval_ticks
        elif self.random_customers and self.elapsed_ticks > self.next_customer_tick:
            self.next_customer_tick = self.elapsed_ticks + self.interval_ticks
            event = self._spawn_customer(tables)
            if event:
                events.append(event)
        return events

    def _spawn_customer(self, tables):
        occupied = {c["table_id"] for c in self.customers}
        free_tables = sorted(
            (table["id"] for table in tables if table["id"] not in occupied),
            key=lambda ident: (ident.rstrip("0123456789"), ident),
        )
        cookable = self.cookable_dishes()
        if not cookable:
            return ("no_dish", {"reason": "no_cookable_dish"})
        if not free_tables:
            return ("no_dish", {"reason": "no_free_table"})

        dish = self.rng.get("customer_dish").choice(cookable)
        table_id = self.rng.get("customer_table").choice(free_tables)
        customer_id = self.ids.new("C")
        reserved = self.reserve(dish)
        if reserved is None:
            return ("no_dish", {"reason": "no_cookable_dish"})
        customer = {
            "id": customer_id,
            "table_id": table_id,
            "dish": dish,
            "state": "waiting",
            "patience_ticks": self.patience_ticks,
            "reserved": reserved,
        }
        self.customers.append(customer)
        return ("customer_arrived", {
            "customer_id": customer_id,
            "table_id": table_id,
            "dish": dish,
            "reserved": dict(reserved),
        })

    def snapshot_customers(self):
        return sort_by_id(self.customers)
