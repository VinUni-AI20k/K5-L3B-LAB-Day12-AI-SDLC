"""Kiểm tra dữ liệu Quán theo số chuẩn Phase 2 (Test Contract v1.1):
- 6 món trong menu với đúng công thức, thời gian nấu cook_s, giá price.
- 2 bếp B1, B2 và 4 bàn T1–T4 với đúng tọa độ.
- day_plan 5 ngày D1–D5: tự tính lại ingredients từ dishes * recipe và đối chiếu với contract.
"""

import unittest
from chonoi.contract import load_contract


class TestPhase2Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract = load_contract()
        cls.tuning = contract["tuning"]
        cls.quan = cls.tuning["quan"]
        cls.menu = cls.tuning["menu"]
        cls.day_plan = cls.tuning["day_plan"]

    def test_stoves_configuration(self):
        """Bếp gồm đúng 2 bếp B1 [2, 8] và B2 [5, 8]."""
        stoves = self.quan.get("stoves", [])
        expected = [
            {"id": "B1", "pos": [2, 8]},
            {"id": "B2", "pos": [5, 8]},
        ]
        self.assertEqual(stoves, expected)

    def test_tables_configuration(self):
        """Bàn gồm đúng 4 bàn T1 [9, 2], T2 [13, 2], T3 [9, 6], T4 [13, 6]."""
        tables = self.quan.get("tables", [])
        expected = [
            {"id": "T1", "pos": [9, 2]},
            {"id": "T2", "pos": [13, 2]},
            {"id": "T3", "pos": [9, 6]},
            {"id": "T4", "pos": [13, 6]},
        ]
        self.assertEqual(tables, expected)

    def test_menu_dishes_and_pricing(self):
        """Menu gồm đủ 6 món chuẩn với recipe, cook_s và price chính xác."""
        expected_menu = {
            "ca_loc_nuong_trui": {
                "recipe": {"ca_loc": 1},
                "cook_s": 6,
                "price": 60,
            },
            "goi_bong_sung": {
                "recipe": {"bong_sung": 2},
                "cook_s": 4,
                "price": 40,
            },
            "lau_ca_linh_dien_dien": {
                "recipe": {"ca_linh": 3, "bong_dien_dien": 1},
                "cook_s": 10,
                "price": 120,
            },
            "canh_chua_ca_loc": {
                "recipe": {"ca_loc": 1, "bong_dien_dien": 1},
                "cook_s": 8,
                "price": 90,
            },
            "ca_keo_nuong": {
                "recipe": {"ca_keo": 2},
                "cook_s": 6,
                "price": 70,
            },
            "lau_mam": {
                "recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
                "cook_s": 12,
                "price": 200,
            },
        }
        self.assertEqual(set(self.menu.keys()), set(expected_menu.keys()))
        for dish_id, exp in expected_menu.items():
            actual = self.menu[dish_id]
            self.assertEqual(actual["recipe"], exp["recipe"], f"Lệch recipe món {dish_id}")
            self.assertEqual(actual["cook_s"], exp["cook_s"], f"Lệch cook_s món {dish_id}")
            self.assertEqual(actual["price"], exp["price"], f"Lệch price món {dish_id}")

    def test_day_plan_recalculation(self):
        """day_plan gồm 5 ngày D1-D5, món thuộc menu, ingredients khớp đúng tổng công thức * số suất."""
        self.assertEqual(len(self.day_plan), 5, "day_plan phải có đúng 5 ngày")

        for idx, plan in enumerate(self.day_plan, start=1):
            self.assertEqual(set(plan), {"day", "dishes", "ingredients"})
            day_val = plan.get("day")
            self.assertEqual(day_val, idx, f"Ngày thứ {idx} phải có day là {idx}")

            dishes = plan.get("dishes", {})
            self.assertTrue(dishes, f"Ngày {day_val} không có dishes")

            # Mọi giá trị trong dishes là số nguyên dương
            for dish_id, count in dishes.items():
                self.assertTrue(isinstance(count, int) and not isinstance(count, bool) and count > 0,
                                f"dishes.{dish_id} của ngày {day_val} phải là số nguyên dương")

            # Mọi giá trị trong ingredients là số nguyên dương
            ingredients = plan.get("ingredients", {})
            for ing_id, qty in ingredients.items():
                self.assertTrue(isinstance(qty, int) and not isinstance(qty, bool) and qty > 0,
                                f"ingredients.{ing_id} của ngày {day_val} phải là số nguyên dương")

            # Mọi món phải nằm trong menu
            for dish_id in dishes:
                self.assertIn(dish_id, self.menu, f"Món {dish_id} của ngày {day_val} không có trong menu")

            # Tự tính lại ingredients
            calculated_ingredients = {}
            for dish_id, count in dishes.items():
                recipe = self.menu[dish_id]["recipe"]
                for item, qty in recipe.items():
                    calculated_ingredients[item] = calculated_ingredients.get(item, 0) + qty * count

            self.assertEqual(
                calculated_ingredients,
                ingredients,
                f"Lệch ingredients tính toán ở ngày {day_val}"
            )


if __name__ == "__main__":
    unittest.main()
