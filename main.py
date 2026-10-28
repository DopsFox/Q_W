import sys
import io
import math
import time
import random
import heapq
import copy
import gc
import tracemalloc
import hashlib
import requests
import dateutil.rrule
import matplotlib.dates
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import re
from typing import Any, cast, Optional, Tuple

import folium
from folium.plugins import BeautifyIcon, PolyLineTextPath
from geopy.distance import geodesic
from geopy.geocoders import Nominatim, ArcGIS, Photon
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QMessageBox, QTableWidgetItem, QHeaderView,
                               QTextEdit, QTableWidget, QAbstractItemView, QDialog,
                               QFileDialog)
from PySide6.QtWebEngineWidgets import QWebEngineView

from ui_main import Ui_MainWindow as Ui_Main
from ui_sf_point import Ui_MainWindow as Ui_SF
from ui_add_point import Ui_MainWindow as Ui_AddPoint
from ui_table_points_reader import Ui_MainWindow as Ui_TablePointsReader


# ==========================================
# 0. КЛАС РОЗУМНОГО ГЕОКОДУВАННЯ (SmartGeocoder)
# ==========================================
class SmartGeocoder:
    ALIASES = [
        (r'миколи\s+руденка', 'Кольцова'),
        (r'руденка\s+миколи', 'Кольцова'),
        (r'руденка', 'Кольцова'),
        (r'загорівськ\w*', 'Багговутівська'),
        (r'воскресенськ\w*\s+пр\w*', 'бульвар Перова'),
        (r'берестейськ\w*\s+пр\w*', 'проспект Перемоги'),
        (r'берестейский\w*\s+пр\w*', 'проспект Перемоги'),
        (r'самійла\s+кішки', 'Маршала Конєва'),
        (r'кішки', 'Маршала Конєва'),
    ]

    def __init__(self):
        self.arcgis = ArcGIS(timeout=10)
        self.nominatim = Nominatim(user_agent="smart_logistics_ua_app", timeout=10)
        self.photon = Photon(user_agent="smart_logistics_ua_app", timeout=10)

    @staticmethod
    def clean_text(text: str) -> str:
        text = text.replace('«', '').replace('»', '').replace('“', '').replace('”', '').replace('"', '').replace("'", '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _query_services(self, query: str, must_be_kyiv: bool = False) -> Optional[Tuple[float, float, str]]:
        try:
            loc = self.nominatim.geocode(query, country_codes="ua")
            if loc and hasattr(loc, 'latitude') and hasattr(loc, 'longitude'):
                lat, lon = float(loc.latitude), float(loc.longitude)
                if not must_be_kyiv or (50.15 <= lat <= 50.65 and 30.15 <= lon <= 30.90):
                    return (lat, lon, str(getattr(loc, 'address', query)))
        except Exception:
            pass

        try:
            loc = self.arcgis.geocode(query)
            if loc and hasattr(loc, 'latitude') and hasattr(loc, 'longitude'):
                lat, lon = float(loc.latitude), float(loc.longitude)
                if not must_be_kyiv or (50.15 <= lat <= 50.65 and 30.15 <= lon <= 30.90):
                    return (lat, lon, str(getattr(loc, 'address', query)))
        except Exception:
            pass

        try:
            loc = self.photon.geocode(f"{query}, Ukraine")
            if loc and hasattr(loc, 'latitude') and hasattr(loc, 'longitude'):
                lat, lon = float(loc.latitude), float(loc.longitude)
                if not must_be_kyiv or (50.15 <= lat <= 50.65 and 30.15 <= lon <= 30.90):
                    return (lat, lon, str(getattr(loc, 'address', query)))
        except Exception:
            pass

        return None

    def geocode(self, address_text: str) -> Optional[Tuple[float, float, str]]:
        if not address_text or not address_text.strip():
            return None
        cleaned = self.clean_text(address_text)
        is_kyiv = "київ" in cleaned.lower()
        query_ua = f"{cleaned}, Україна" if "Україна" not in cleaned else cleaned

        res = self._query_services(query_ua, must_be_kyiv=is_kyiv)
        if res:
            return res

        if is_kyiv:
            alias_query = cleaned
            for pattern, replacement in self.ALIASES:
                alias_query = re.sub(pattern, replacement, alias_query, flags=re.IGNORECASE)
            if alias_query != cleaned:
                alias_query_ua = f"{alias_query}, Україна" if "Україна" not in alias_query else alias_query
                res = self._query_services(alias_query_ua, must_be_kyiv=True)
                if res:
                    return res

        parts = [p.strip() for p in cleaned.split(',') if p.strip()]
        if len(parts) > 1:
            street_city_parts = [
                p for p in parts
                if not re.match(r'^\d+[\w/-]*$', p)
                and 'виділ' not in p.lower()
                and 'квартал' not in p.lower()
                and 'буд' not in p.lower()
                and 'корп' not in p.lower()
            ]
            street_city = ', '.join(street_city_parts)
            if street_city and street_city != cleaned:
                res = self._query_services(f"{street_city}, Україна", must_be_kyiv=is_kyiv)
                if res:
                    return (res[0], res[1], f"{cleaned} (орієнтир: {res[2]})")

        if len(parts) > 1:
            city_only = parts[-1]
            try:
                loc = self.arcgis.geocode(f"{city_only}, Україна")
                if loc and hasattr(loc, 'latitude') and hasattr(loc, 'longitude'):
                    return (float(loc.latitude), float(loc.longitude), f"{cleaned} (центр: {getattr(loc, 'address', city_only)})")
            except Exception:
                pass

        return None


# ==========================================
# 1. КЛАС ЛОГІКИ ТОЧОК (Зберігання даних)
# ==========================================
class PointsManager:
    def __init__(self):
        self.start = None
        self.finish = None
        self.waypoints = []

    def set_start(self, data):
        self.start = data

    def set_finish(self, data):
        self.finish = data

    def add_waypoint(self, data):
        self.waypoints.append(data)

    def has_start(self):
        return self.start is not None

    def has_finish(self):
        return self.finish is not None

    def clear_all(self):
        self.start = None
        self.finish = None
        self.waypoints = []


# ==========================================
# 1.1 КЛАСИ УПРАВЛІННЯ СТАНОМ ТА ІСТОРІЄЮ ДІЙ (Undo / Redo)
# ==========================================
class AppState:
    def __init__(
        self,
        start: Optional[dict] = None,
        finish: Optional[dict] = None,
        waypoints: Optional[list[dict]] = None,
        last_route: Optional[list] = None,
        last_route_color: str = "#FFFF00",
        calc_metrics: Optional[list[tuple[str, str]]] = None,
        algo_results: Optional[dict] = None,
        current_points_hash: Optional[str] = None,
        search_method_index: int = 0,
        route_type_index: int = 0
    ):
        self.start = copy.deepcopy(start)
        self.finish = copy.deepcopy(finish)
        self.waypoints = copy.deepcopy(waypoints) if waypoints is not None else []
        self.last_route = copy.deepcopy(last_route)
        self.last_route_color = last_route_color
        self.calc_metrics = copy.deepcopy(calc_metrics) if calc_metrics is not None else []
        self.algo_results = copy.deepcopy(algo_results) if algo_results is not None else {}
        self.current_points_hash = current_points_hash
        self.search_method_index = search_method_index
        self.route_type_index = route_type_index

    def clear(self):
        self.start = None
        self.finish = None
        self.waypoints.clear()
        self.last_route = None
        self.calc_metrics.clear()
        self.algo_results.clear()
        self.current_points_hash = None


class HistoryManager:
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history: list[AppState] = []
        self.current_index: int = -1

    def push_state(self, state: AppState):
        if self.current_index < len(self.history) - 1:
            for s in self.history[self.current_index + 1:]:
                s.clear()
            self.history = self.history[:self.current_index + 1]

        self.history.append(state)
        if len(self.history) > self.max_history:
            removed = self.history.pop(0)
            removed.clear()
        self.current_index = len(self.history) - 1

    def can_undo(self) -> bool:
        return self.current_index > 0

    def can_redo(self) -> bool:
        return 0 <= self.current_index < len(self.history) - 1

    def undo(self) -> Optional[AppState]:
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return None

    def redo(self) -> Optional[AppState]:
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return None

    def clear(self):
        for s in self.history:
            s.clear()
        self.history.clear()
        self.current_index = -1


# ==========================================
# 2. КЛАС АЛГОРИТМІВ (Математична логіка)
# ==========================================
class RouteCalculator:
    @staticmethod
    def a_star_sort_waypoints(start_coord, finish_coord, waypoints, mode=1):
        if not waypoints:
            return []

        num_wp = len(waypoints)
        initial_state: tuple[float, float, int, tuple[int, ...], list[int]] = (0.0, 0.0, -1, (), [])
        pq: list[tuple[float, float, int, tuple[int, ...], list[int]]] = []
        heapq.heappush(pq, initial_state)
        visited_states = set()

        def heuristic(curr_idx, visited):
            unvisited = [i for i in range(num_wp) if i not in visited]
            if not unvisited:
                curr_coord = start_coord if curr_idx == -1 else waypoints[curr_idx]['coord']
                return geodesic(curr_coord, finish_coord).meters

            curr_coord = start_coord if curr_idx == -1 else waypoints[curr_idx]['coord']
            min_dist = min(geodesic(curr_coord, waypoints[i]['coord']).meters for i in unvisited)
            return min_dist

        while pq:
            f, g, curr_idx, visited, path = heapq.heappop(pq)

            if len(visited) == num_wp:
                return [waypoints[i] for i in path]

            state_key = (curr_idx, visited)
            if state_key in visited_states:
                continue
            visited_states.add(state_key)

            curr_coord = start_coord if curr_idx == -1 else waypoints[curr_idx]['coord']
            unvisited = [i for i in range(num_wp) if i not in visited]

            if unvisited:
                min_priority = min(waypoints[i].get('priority', 3) for i in unvisited)
                if mode == 1:
                    valid_next = [i for i in unvisited if waypoints[i].get('priority', 3) == min_priority]
                else:
                    valid_next = unvisited
            else:
                min_priority = 0
                valid_next = []

            for next_idx in valid_next:
                next_coord = waypoints[next_idx]['coord']
                step_cost = geodesic(curr_coord, next_coord).meters


                priority_diff = waypoints[next_idx].get('priority', 3) - min_priority
                if priority_diff > 0:
                    boxes = waypoints[next_idx].get('boxes', 1)


                    if mode == 3:
                        alpha = 0.5
                        w_base = 20000.0
                        penalty = w_base * priority_diff * math.exp(-alpha * boxes)
                        step_cost += penalty


                    elif mode == 4:
                        w_max = 50000.0
                        k = 1.5
                        b_th = 3.5
                        penalty = w_max * priority_diff * (1.0 / (1.0 + math.exp(-k * (boxes - b_th))))
                        step_cost += penalty

                new_g = g + step_cost
                new_visited = tuple(sorted(list(visited) + [next_idx]))
                new_path = path + [next_idx]

                h = heuristic(next_idx, new_visited)
                new_f = new_g + h

                heapq.heappush(pq, (new_f, new_g, next_idx, new_visited, new_path))

        return waypoints

    @staticmethod
    def dijkstra_sort_waypoints(start_coord, finish_coord, waypoints, mode=1):
        if not waypoints:
            return []

        num_wp = len(waypoints)
        initial_state: tuple[float, int, tuple[int, ...], list[int]] = (0.0, -1, (), [])
        pq: list[tuple[float, int, tuple[int, ...], list[int]]] = []
        heapq.heappush(pq, initial_state)
        visited_states = set()

        while pq:
            g, curr_idx, visited, path = heapq.heappop(pq)

            if len(visited) == num_wp:
                return [waypoints[i] for i in path]

            state_key = (curr_idx, visited)
            if state_key in visited_states:
                continue
            visited_states.add(state_key)

            curr_coord = start_coord if curr_idx == -1 else waypoints[curr_idx]['coord']
            unvisited = [i for i in range(num_wp) if i not in visited]

            if unvisited:
                min_priority = min(waypoints[i].get('priority', 3) for i in unvisited)
                if mode == 1:
                    valid_next = [i for i in unvisited if waypoints[i].get('priority', 3) == min_priority]
                else:
                    valid_next = unvisited
            else:
                min_priority = 0
                valid_next = []

            for next_idx in valid_next:
                next_coord = waypoints[next_idx]['coord']
                step_cost = geodesic(curr_coord, next_coord).meters

                priority_diff = waypoints[next_idx].get('priority', 3) - min_priority
                if priority_diff > 0:
                    boxes = waypoints[next_idx].get('boxes', 1)

                    if mode == 3:
                        alpha = 0.5
                        w_base = 20000.0
                        penalty = w_base * priority_diff * math.exp(-alpha * boxes)
                        step_cost += penalty

                    elif mode == 4:
                        w_max = 50000.0
                        k = 1.5
                        b_th = 3.5
                        penalty = w_max * priority_diff * (1.0 / (1.0 + math.exp(-k * (boxes - b_th))))
                        step_cost += penalty

                new_g = g + step_cost
                new_visited = tuple(sorted(list(visited) + [next_idx]))
                new_path = path + [next_idx]

                heapq.heappush(pq, (new_g, next_idx, new_visited, new_path))

        return waypoints

    @staticmethod
    def aco_sort_waypoints(start_coord, finish_coord, waypoints, mode=1):
        if not waypoints:
            return []

        points = [start_coord] + [wp['coord'] for wp in waypoints] + [finish_coord]
        n_nodes = len(points)
        num_wp = len(waypoints)

        dist = [[0.0] * n_nodes for _ in range(n_nodes)]
        for i in range(n_nodes):
            for j in range(n_nodes):
                if i != j:
                    dist[i][j] = geodesic(points[i], points[j]).meters
                    if dist[i][j] == 0: dist[i][j] = 1e-5

        n_ants = max(10, num_wp * 2)
        n_iterations = 50
        alpha_aco = 1.0
        beta = 2.0
        evaporation_rate = 0.5
        q = 1000.0

        pheromone = [[1.0] * n_nodes for _ in range(n_nodes)]
        best_path_indices: list[int] = list(range(1, num_wp + 1))
        best_path_length = float('inf')

        for _ in range(n_iterations):
            all_paths = []

            for ant in range(n_ants):
                path = []
                visited = set()
                current_node = 0
                path_length = 0.0

                for _ in range(num_wp):
                    unvisited = [node for node in range(1, num_wp + 1) if node not in visited]
                    min_priority = min(waypoints[node - 1].get('priority', 3) for node in unvisited)

                    if mode == 1:
                        valid_next = [node for node in unvisited if
                                      waypoints[node - 1].get('priority', 3) == min_priority]
                    else:
                        valid_next = unvisited

                    probabilities = []
                    sum_prob = 0.0

                    for next_node in valid_next:
                        actual_dist = dist[current_node][next_node]
                        effective_dist = actual_dist

                        wp_idx = next_node - 1
                        priority_diff = waypoints[wp_idx].get('priority', 3) - min_priority

                        if priority_diff > 0:
                            boxes = waypoints[wp_idx].get('boxes', 1)
                            if mode == 3:
                                alpha = 0.5
                                w_base = 20000.0
                                effective_dist += w_base * priority_diff * math.exp(-alpha * boxes)
                            elif mode == 4:
                                w_max = 50000.0
                                k = 1.5
                                b_th = 3.5
                                effective_dist += w_max * priority_diff * (1.0 / (1.0 + math.exp(-k * (boxes - b_th))))

                        tau = pheromone[current_node][next_node] ** alpha_aco
                        eta = (1.0 / effective_dist) ** beta
                        prob = tau * eta
                        probabilities.append((next_node, prob))
                        sum_prob += prob

                    if sum_prob > 0:
                        rand_val = random.uniform(0, sum_prob)
                        cumulative = 0.0
                        chosen_node = valid_next[-1]
                        for node, p in probabilities:
                            cumulative += p
                            if cumulative >= rand_val:
                                chosen_node = node
                                break
                    else:
                        chosen_node = random.choice(valid_next)

                    path.append(chosen_node)
                    visited.add(chosen_node)
                    path_length += dist[current_node][chosen_node]
                    current_node = chosen_node

                path_length += dist[current_node][n_nodes - 1]

                all_paths.append((path, path_length))
                if path_length < best_path_length:
                    best_path_length = path_length
                    best_path_indices = path

            for i in range(n_nodes):
                for j in range(n_nodes):
                    pheromone[i][j] *= (1.0 - evaporation_rate)

            for path, length in all_paths:
                pheromone_contribution = q / length
                pheromone[0][path[0]] += pheromone_contribution
                for i in range(len(path) - 1):
                    pheromone[path[i]][path[i + 1]] += pheromone_contribution
                pheromone[path[-1]][n_nodes - 1] += pheromone_contribution

        if not best_path_indices:
            return waypoints
        return [waypoints[i - 1] for i in best_path_indices]

    @staticmethod
    def get_road_route(coords_list):
        coord_strings = [f"{lon},{lat}" for lat, lon in coords_list]
        coords_joined = ";".join(coord_strings)
        url = f"http://router.project-osrm.org/route/v1/driving/{coords_joined}?overview=full&geometries=geojson"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("code") == "Ok":
                route = data["routes"][0]
                distance = route["distance"]
                duration = route["duration"]
                geometry = route["geometry"]["coordinates"]
                folium_route = [[lat, lon] for lon, lat in geometry]
                legs_durations = [leg["duration"] for leg in route.get("legs", [])]
                return folium_route, distance, duration, legs_durations
        except Exception as e:
            print(f"Помилка OSRM: {e}")
        return None, 0, 0, []


# ==========================================
# 3. КЛАС УПРАВЛІННЯ КАРТОЮ (Візуалізація)
# ==========================================
class MapRenderer:
    @staticmethod
    def generate_map_html(points_manager, route_coords=None, route_color="#FFFF00"):
        center_location = points_manager.start['coord'] if points_manager.start else [50.4501, 30.5234]
        zoom = 10 if (points_manager.start and points_manager.finish) else 12

        m = folium.Map(location=center_location, zoom_start=zoom, control_scale=True)

        if points_manager.start:
            eta_str = ""
            if 'eta' in points_manager.start:
                eta_str = f" | ETA: {int(points_manager.start['eta'])} хв"
            folium.Marker(
                points_manager.start['coord'], popup=f"СТАРТ: {points_manager.start['address']}{eta_str}",
                icon=cast(Any, BeautifyIcon(icon_shape='marker', text_color='white', background_color='#28a745', number='S',
                                            inner_icon_style='font-size:14px; font-weight:bold; padding-top:2px;'))
            ).add_to(m)

        if points_manager.finish:
            eta_str = ""
            if 'eta' in points_manager.finish:
                mins = int(points_manager.finish['eta'])
                h, m_mins = divmod(mins, 60)
                eta_str = f" | ETA: {h}г {m_mins}хв" if h > 0 else f" | ETA: {m_mins}хв"
            folium.Marker(
                points_manager.finish['coord'], popup=f"ФІНІШ: {points_manager.finish['address']}{eta_str}",
                icon=cast(Any, BeautifyIcon(icon_shape='marker', text_color='white', background_color='#dc3545', number='F',
                                            inner_icon_style='font-size:14px; font-weight:bold; padding-top:2px;'))
            ).add_to(m)

        for idx, wp in enumerate(points_manager.waypoints):
            priority = wp.get('priority', 3)
            if priority == 1:
                bg_color = '#fd7e14'
            elif priority == 2:
                bg_color = '#ffc107'
            else:
                bg_color = '#007bff'

            eta_str = ""
            if 'eta' in wp:
                mins = int(wp['eta'])
                h, m_mins = divmod(mins, 60)
                eta_str = f" <br><b>Прибуття:</b> {h}г {m_mins}хв" if h > 0 else f" <br><b>Прибуття:</b> {m_mins}хв"

            popup_html = f"Точка {idx + 1} (Пріоритет: {priority})<br>{wp['address']}<br>Час на точці: {wp['time']} хв. (+10){eta_str}"

            folium.Marker(
                wp['coord'], popup=folium.Popup(popup_html, max_width=300),
                icon=cast(Any, BeautifyIcon(icon_shape='marker', text_color='white', background_color=bg_color,
                                            number=str(idx + 1),
                                            inner_icon_style='font-size:14px; font-weight:bold; padding-top:2px;'))
            ).add_to(m)

        if route_coords:
            route_line = folium.PolyLine(
                route_coords,
                color=route_color,
                weight=5,
                opacity=0.9
            )
            route_line.add_to(m)

            PolyLineTextPath(
                route_line,
                '►',
                repeat=True,
                offset=5,
                attributes={'fill': '#000000', 'font-weight': 'bold', 'font-size': '15'}
            ).add_to(m)

        data = io.BytesIO()
        m.save(data, close_file=False)
        return data.getvalue().decode()


# ==========================================
# 4. ВІКНА ІНТЕРФЕЙСУ ТА ГОЛОВНЕ ВІКНО ДОДАТКУ
# ==========================================
class StartFinishWindow(QMainWindow):
    def __init__(self, callback_save):
        super().__init__()
        self.ui = Ui_SF()
        self.ui.setupUi(self)
        self.resize(627, 203)
        self.setMinimumSize(627, 203)
        self.callback_save = callback_save
        self.mode = None
        self.geocoder = SmartGeocoder()
        self.ui.pushButton_add_start_finish.clicked.connect(self.process_input)

    def set_mode(self, mode):
        self.mode = mode
        title = "Додати СТАРТ" if mode == 'start' else "Додати ФІНІШ"
        self.setWindowTitle(title)
        self.ui.pushButton_add_start_finish.setText(title)
        self.ui.textEdit_text_adress_start_finish.clear()
        self.ui.textEdit_coordinates_address_start_finish.clear()

    def process_input(self):
        address_text = self.ui.textEdit_text_adress_start_finish.toPlainText().strip()
        coords_text = self.ui.textEdit_coordinates_address_start_finish.toPlainText().strip()
        lat, lon, resolved_address = None, None, ""

        if address_text:
            try:
                res = self.geocoder.geocode(address_text)
                if res:
                    lat, lon, resolved_address = res
                else:
                    QMessageBox.warning(self, "Помилка", "Адресу не знайдено.")
                    return
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося знайти адресу: {e}")
                return
        elif coords_text:
            try:
                lat_str, lon_str = coords_text.replace(' ', '').split(',')
                lat, lon = float(lat_str), float(lon_str)
                resolved_address = f"Задано координатами ({lat}, {lon})"
            except:
                QMessageBox.warning(self, "Помилка", "Неправильний формат координат.")
                return
        else:
            QMessageBox.warning(self, "Помилка", "Заповніть поле.")
            return

        data = {'coord': [lat, lon], 'address': resolved_address, 'boxes': 0, 'time': 0}
        self.callback_save(self.mode, data)
        self.close()


class WaypointWindow(QMainWindow):
    def __init__(self, callback_save):
        super().__init__()
        self.ui = Ui_AddPoint()
        self.ui.setupUi(self)
        self.resize(653, 400)
        self.setMinimumSize(653, 400)
        self.callback_save = callback_save
        self.geocoder = SmartGeocoder()
        self.ui.pushButton_add_new_point_dialog.clicked.connect(self.process_input)

        self.edit_index = None

        self.ui.comboBox_priority.clear()
        self.ui.comboBox_priority.addItems([
            "1 - Високий пріоритет",
            "2 - Середній пріоритет",
            "3 - Звичайний пріоритет"
        ])

    def _get_val(self, text_edit):
        text = text_edit.toPlainText().strip()
        return int(text) if text else 0

    def clear_fields(self):
        self.edit_index = None
        for text_edit in self.findChildren(QTextEdit):
            text_edit.clear()
        self.ui.comboBox_priority.setCurrentIndex(2)
        self.setWindowTitle("Додати нову точку")

    def load_data(self, data, edit_index):
        self.edit_index = edit_index

        address = data.get('address', '')
        if "Координати:" not in address:
            self.ui.textEdit_text_adress.setText(address)
        self.ui.textEdit_coordinates_address.setText(f"{data['coord'][0]}, {data['coord'][1]}")

        priority = data.get('priority', 3)
        index = self.ui.comboBox_priority.findText(f"{priority} -", Qt.MatchFlag.MatchStartsWith)
        if index >= 0:
            self.ui.comboBox_priority.setCurrentIndex(index)

        raw = data.get('raw_orders', {})

        def set_val(edit_widget, val):
            edit_widget.setText(str(val) if val else "")

        set_val(self.ui.textEdit_ghee_1l, raw.get('ghee_1l', 0))
        set_val(self.ui.textEdit_ghee_500ml, raw.get('ghee_500ml', 0))
        set_val(self.ui.textEdit_ghee_300ml, raw.get('ghee_300ml', 0))
        set_val(self.ui.textEdit_ghee_100ml, raw.get('ghee_100ml', 0))
        set_val(self.ui.textEdit_ghee_25ml, raw.get('ghee_25ml', 0))
        set_val(self.ui.textEdit_sesame_seeds, raw.get('sesame_seeds', 0))
        set_val(self.ui.textEdit_milk_thistle, raw.get('milk_thistle', 0))
        set_val(self.ui.textEdit_flax, raw.get('flax', 0))
        set_val(self.ui.textEdit_mustard, raw.get('mustard', 0))
        set_val(self.ui.textEdit_sea_buckthorn, raw.get('sea_buckthorn', 0))
        set_val(self.ui.textEdit_buckwheat_honey_500ml, raw.get('buckwheat_honey_500ml', 0))
        set_val(self.ui.textEdit_buckwheat_honey_300ml, raw.get('buckwheat_honey_300ml', 0))
        set_val(self.ui.textEdit_wildflower_honey_500ml, raw.get('wildflower_honey_500ml', 0))
        set_val(self.ui.textEdit_wildflower_honey_300ml, raw.get('wildflower_honey_300ml', 0))

    def process_input(self):
        try:
            ghee_1l = self._get_val(self.ui.textEdit_ghee_1l)
            ghee_500 = self._get_val(self.ui.textEdit_ghee_500ml)
            ghee_300 = self._get_val(self.ui.textEdit_ghee_300ml)
            ghee_100 = self._get_val(self.ui.textEdit_ghee_100ml)
            ghee_25 = self._get_val(self.ui.textEdit_ghee_25ml)
            oil_sesame = self._get_val(self.ui.textEdit_sesame_seeds)
            oil_milk = self._get_val(self.ui.textEdit_milk_thistle)
            oil_flax = self._get_val(self.ui.textEdit_flax)
            oil_mustard = self._get_val(self.ui.textEdit_mustard)
            oil_sea = self._get_val(self.ui.textEdit_sea_buckthorn)
            honey_buck_500 = self._get_val(self.ui.textEdit_buckwheat_honey_500ml)
            honey_buck_300 = self._get_val(self.ui.textEdit_buckwheat_honey_300ml)
            honey_wild_500 = self._get_val(self.ui.textEdit_wildflower_honey_500ml)
            honey_wild_300 = self._get_val(self.ui.textEdit_wildflower_honey_300ml)
        except ValueError:
            QMessageBox.warning(self, "Помилка вводу", "Кількість баночок має бути цілим числом!")
            return

        errors = []
        total_500 = ghee_500 + honey_buck_500 + honey_wild_500
        total_300 = ghee_300 + honey_buck_300 + honey_wild_300
        total_oils = oil_sesame + oil_milk + oil_flax + oil_mustard + oil_sea

        if ghee_1l % 3 != 0: errors.append(" 1 л (Гхі) фасується кратно 3 шт.")
        if total_500 % 6 != 0: errors.append(" 500 мл (Гхі та Мед) фасуються кратно 6 шт.")
        if total_300 % 12 != 0: errors.append(" 300 мл (Гхі та Мед) фасуються кратно 12 шт.")
        if ghee_100 % 12 != 0: errors.append(" 100 мл (Гхі) фасується кратно 12 шт.")
        if total_oils % 12 != 0: errors.append(" Олії (250/300 мл) фасуються кратно 12 шт.")

        if errors:
            rules = "\n\nПравила фасування:\n- 1 л: 3 шт/коробка\n- 500 мл: 6 шт/коробка\n- 100/250/300 мл: 12 шт/коробка"
            QMessageBox.warning(self, "Помилка фасування", "\n".join(errors) + rules)
            return

        boxes = (ghee_1l // 3) + (total_500 // 6) + (total_300 // 12) + (ghee_100 // 12) + (total_oils // 12)
        if boxes == 0:
            QMessageBox.warning(self, "Порожнє замовлення", "Додайте товари для розрахунку.")
            return

        time_minutes = boxes * 2

        priority_text = self.ui.comboBox_priority.currentText()
        priority = int(priority_text.split('-')[0].strip()) if priority_text else 3

        address_text = self.ui.textEdit_text_adress.toPlainText().strip()
        coords_text = self.ui.textEdit_coordinates_address.toPlainText().strip()
        lat, lon, resolved_address = None, None, ""

        if address_text:
            try:
                res = self.geocoder.geocode(address_text)
                if res:
                    lat, lon, resolved_address = res
                else:
                    QMessageBox.warning(self, "Помилка", "Адресу не знайдено.")
                    return
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося знайти адресу: {e}")
                return
        elif coords_text:
            try:
                lat_str, lon_str = coords_text.replace(' ', '').split(',')
                lat, lon = float(lat_str), float(lon_str)
                resolved_address = f"Координати: ({lat}, {lon})"
            except:
                QMessageBox.warning(self, "Помилка", "Неправильний формат координат.")
                return
        else:
            QMessageBox.warning(self, "Помилка", "Заповніть адресу або координати.")
            return

        raw_orders = {
            'ghee_1l': ghee_1l, 'ghee_500ml': ghee_500, 'ghee_300ml': ghee_300,
            'ghee_100ml': ghee_100, 'ghee_25ml': ghee_25,
            'sesame_seeds': oil_sesame, 'milk_thistle': oil_milk, 'flax': oil_flax,
            'mustard': oil_mustard, 'sea_buckthorn': oil_sea,
            'buckwheat_honey_500ml': honey_buck_500, 'buckwheat_honey_300ml': honey_buck_300,
            'wildflower_honey_500ml': honey_wild_500, 'wildflower_honey_300ml': honey_wild_300
        }

        data = {
            'coord': [lat, lon],
            'address': resolved_address,
            'boxes': boxes,
            'time': time_minutes,
            'priority': priority,
            'raw_orders': raw_orders
        }

        self.callback_save(data, self.edit_index)
        self.close()


class TablePointsReaderWindow(QMainWindow):
    def __init__(self, callback_import_points):
        super().__init__()
        self.ui = Ui_TablePointsReader()
        self.ui.setupUi(self)
        self.resize(463, 710)
        self.setMinimumSize(463, 710)
        self.callback_import_points = callback_import_points
        self.geocoder = SmartGeocoder()
        self.loaded_addresses: list[dict] = []

        self.setup_table()

        self.ui.pushButton_select_file.clicked.connect(self.select_file)
        self.ui.pushButton_get_selected_points.clicked.connect(self.process_selected_points)

    def setup_table(self):
        self.ui.tableWidget_select_points.setColumnCount(3)
        self.ui.tableWidget_select_points.setHorizontalHeaderLabels(["Вибір", "№", "Адреса"])
        self.ui.tableWidget_select_points.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.ui.tableWidget_select_points.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть файл з адресами",
            "",
            "Текстові файли (*.txt *.csv *.json);;Всі файли (*.*)"
        )
        if not file_path:
            return

        addresses = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if file_path.endswith('.json'):
                import json
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str) and item.strip():
                            addresses.append(item.strip())
                        elif isinstance(item, dict) and 'address' in item:
                            addresses.append(str(item['address']).strip())
            elif file_path.endswith('.csv'):
                import csv
                reader = csv.reader(content.splitlines())
                for row in reader:
                    if row:
                        addr = row[0].strip()
                        if addr and addr.lower() != 'address' and addr.lower() != 'адреса':
                            addresses.append(addr)
            else:
                for line in content.splitlines():
                    cleaned = line.strip()
                    if cleaned:
                        addresses.append(cleaned)
        except Exception as e:
            QMessageBox.critical(self, "Помилка читання файлу", f"Не вдалося прочитати файл:\n{e}")
            return

        if not addresses:
            QMessageBox.warning(self, "Порожній файл", "У вибраному файлі не знайдено адрес.")
            return

        self.populate_table(addresses)

    def populate_table(self, addresses: list[str]):
        self.loaded_addresses = [{'address': addr, 'boxes': random.randint(1, 10), 'priority': 3} for addr in addresses]
        self.ui.tableWidget_select_points.setRowCount(0)

        for row, item_data in enumerate(self.loaded_addresses):
            self.ui.tableWidget_select_points.insertRow(row)

            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked)
            self.ui.tableWidget_select_points.setItem(row, 0, chk_item)

            num_item = QTableWidgetItem(str(row + 1))
            num_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.ui.tableWidget_select_points.setItem(row, 1, num_item)

            addr_item = QTableWidgetItem(item_data['address'])
            addr_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.ui.tableWidget_select_points.setItem(row, 2, addr_item)

    def process_selected_points(self):
        selected_items = []
        for row in range(self.ui.tableWidget_select_points.rowCount()):
            chk = self.ui.tableWidget_select_points.item(row, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                if row < len(self.loaded_addresses):
                    selected_items.append(self.loaded_addresses[row])

        if not selected_items:
            QMessageBox.warning(self, "Не вибрано адрес", "Будь ласка, відзначте прапорцями хоча б одну адресу.")
            return

        self.ui.pushButton_get_selected_points.setEnabled(False)
        self.ui.pushButton_get_selected_points.setText(f"Геокодування (0/{len(selected_items)})...")
        QApplication.processEvents()

        imported_points = []
        not_found = []

        for idx, item in enumerate(selected_items):
            addr = item['address']
            self.ui.pushButton_get_selected_points.setText(f"Геокодування ({idx + 1}/{len(selected_items)})...")
            QApplication.processEvents()
            try:
                time.sleep(0.3)
                res = self.geocoder.geocode(addr)
                if res:
                    lat, lon, resolved_addr = res
                    boxes = item.get('boxes', random.randint(1, 10))
                    time_minutes = boxes * 2
                    priority = item.get('priority', 3)
                    wp_data = {
                        'coord': [lat, lon],
                        'address': addr,
                        'boxes': boxes,
                        'time': time_minutes,
                        'priority': priority,
                        'raw_orders': {}
                    }
                    imported_points.append(wp_data)
                else:
                    not_found.append(addr)
            except Exception as e:
                not_found.append(f"{addr} ({e})")

        self.ui.pushButton_get_selected_points.setEnabled(True)
        self.ui.pushButton_get_selected_points.setText("Підтвердити вибрані адреси")

        if imported_points:
            self.callback_import_points(imported_points)
            msg = f"Успішно імпортовано точок: {len(imported_points)}."
            if not_found:
                msg += f"\n\nНе вдалося знайти {len(not_found)} адрес:\n- " + "\n- ".join(not_found[:5])
                if len(not_found) > 5:
                    msg += f"\n... та ще {len(not_found) - 5}"
            QMessageBox.information(self, "Імпорт завершено", msg)
            self.close()
        else:
            QMessageBox.warning(self, "Помилка геокодування", "Жодної з вибраних адрес не вдалося знайти на карті.")


class RouteOptimizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Main()
        self.ui.setupUi(self)
        self.resize(1082, 851)
        self.setMinimumSize(1082, 851)

        self.points = PointsManager()
        self.router = RouteCalculator()

        self.sf_window = StartFinishWindow(self.save_sf_point)
        self.wp_window = WaypointWindow(self.save_waypoint)
        self.points_reader_window = TablePointsReaderWindow(self.add_imported_points)

        self.map_layout = QVBoxLayout(self.ui.widget_map_container)
        self.map_layout.setContentsMargins(0, 0, 0, 0)
        self.web_view = QWebEngineView()
        self.map_layout.addWidget(self.web_view)

        self.ui.comboBox_search_method.clear()
        self.ui.comboBox_search_method.addItems([
            "A* (А-зірка)",
            "Алгоритм Дейкстри",
            "Мурашиний алгоритм"
        ])

        self.ui.comboBox_rout_type.clear()
        self.ui.comboBox_rout_type.addItems([
            "1. Слідувати пріоритетам",
            "2. Ігнорування пріоритетів",
            "3. Часткове ігнор. (Експоненційне згасання)",
            "4. Часткове ігнор. (Логістична функція)"
        ])

        self.last_route = None
        self.last_route_color = "#FFFF00"
        self.current_points_hash = None
        self.algo_results = {}
        self._is_restoring = False

        self.history = HistoryManager(max_history=50)

        self.setup_table()
        self.setup_calculation_table()
        self.update_map_view()

        self.ui.pushButton_back.clicked.connect(self.undo_action)
        self.ui.pushButton_forward.clicked.connect(self.redo_action)

        self.ui.pushButton_calculate_route.clicked.connect(self.calculate_and_draw)
        self.ui.pushButton_add_start.clicked.connect(lambda: self.sf_window.set_mode('start') or self.sf_window.show())
        self.ui.pushButton_add_finish.clicked.connect(
            lambda: self.sf_window.set_mode('finish') or self.sf_window.show())

        self.ui.pushButton_add_new_point.clicked.connect(self.open_new_waypoint)
        self.ui.pushButton_delete_point.clicked.connect(self.delete_selected_point)
        self.ui.pushButton_edit_delivery.clicked.connect(self.edit_selected_point)
        self.ui.pushButton_regular_deliveries.clicked.connect(self.load_regular_deliveries)
        self.ui.pushButton_open_points_file.clicked.connect(self.points_reader_window.show)

        self.ui.pushButton_save_route.setText("Аналітика (Графіки)")
        self.ui.pushButton_save_route.clicked.connect(self.show_analytics_graphs)

        self.record_state()

    def get_current_calc_metrics(self) -> list[tuple[str, str]]:
        metrics = []
        for r in range(self.ui.tableWidget_calculation.rowCount()):
            item0 = self.ui.tableWidget_calculation.item(r, 0)
            item1 = self.ui.tableWidget_calculation.item(r, 1)
            if item0 and item1:
                metrics.append((item0.text(), item1.text()))
        return metrics

    def set_calc_metrics(self, metrics: list[tuple[str, str]]):
        self.ui.tableWidget_calculation.setRowCount(0)
        for row, (param, value) in enumerate(metrics):
            self.ui.tableWidget_calculation.insertRow(row)
            self.ui.tableWidget_calculation.setItem(row, 0, QTableWidgetItem(param))
            self.ui.tableWidget_calculation.setItem(row, 1, QTableWidgetItem(value))

    def update_nav_buttons(self):
        self.ui.pushButton_back.setEnabled(self.history.can_undo())
        self.ui.pushButton_forward.setEnabled(self.history.can_redo())

    def record_state(self):
        if getattr(self, '_is_restoring', False):
            return
        state = AppState(
            start=self.points.start,
            finish=self.points.finish,
            waypoints=self.points.waypoints,
            last_route=self.last_route,
            last_route_color=self.last_route_color,
            calc_metrics=self.get_current_calc_metrics(),
            algo_results=self.algo_results,
            current_points_hash=self.current_points_hash,
            search_method_index=self.ui.comboBox_search_method.currentIndex(),
            route_type_index=self.ui.comboBox_rout_type.currentIndex()
        )
        self.history.push_state(state)
        self.update_nav_buttons()

    def undo_action(self):
        state = self.history.undo()
        if state is not None:
            self.restore_state(state)

    def redo_action(self):
        state = self.history.redo()
        if state is not None:
            self.restore_state(state)

    def restore_state(self, state: AppState):
        if not state:
            return
        self._is_restoring = True
        try:
            self.points.start = copy.deepcopy(state.start)
            self.points.finish = copy.deepcopy(state.finish)
            self.points.waypoints = copy.deepcopy(state.waypoints)
            self.last_route = copy.deepcopy(state.last_route)
            self.last_route_color = state.last_route_color
            self.algo_results = copy.deepcopy(state.algo_results)
            self.current_points_hash = state.current_points_hash

            if 0 <= state.search_method_index < self.ui.comboBox_search_method.count():
                self.ui.comboBox_search_method.setCurrentIndex(state.search_method_index)
            if 0 <= state.route_type_index < self.ui.comboBox_rout_type.count():
                self.ui.comboBox_rout_type.setCurrentIndex(state.route_type_index)

            self.set_calc_metrics(state.calc_metrics)
            self.update_table_view()
            self.update_map_view(route=self.last_route, route_color=self.last_route_color)
            self.update_nav_buttons()
        finally:
            self._is_restoring = False

    def setup_table(self):

        self.ui.tableWidget_waypoints.setColumnCount(7)
        self.ui.tableWidget_waypoints.setHorizontalHeaderLabels(
            ["Тип/№", "Адреса", "Широта", "Довгота", "Коробки", "Час (хв)", "Прибуття"])

        self.ui.tableWidget_waypoints.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        header = self.ui.tableWidget_waypoints.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

    def setup_calculation_table(self):
        self.ui.tableWidget_calculation.setColumnCount(2)
        self.ui.tableWidget_calculation.setHorizontalHeaderLabels(["Параметр", "Значення"])
        header = self.ui.tableWidget_calculation.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def update_table_view(self):
        self.ui.tableWidget_waypoints.setRowCount(0)
        row = 0

        def add_row(p_type, address, lat, lon, boxes, time, eta_str):
            self.ui.tableWidget_waypoints.insertRow(row)
            self.ui.tableWidget_waypoints.setItem(row, 0, QTableWidgetItem(p_type))
            self.ui.tableWidget_waypoints.setItem(row, 1, QTableWidgetItem(address))
            self.ui.tableWidget_waypoints.setItem(row, 2, QTableWidgetItem(str(round(lat, 5))))
            self.ui.tableWidget_waypoints.setItem(row, 3, QTableWidgetItem(str(round(lon, 5))))
            self.ui.tableWidget_waypoints.setItem(row, 4, QTableWidgetItem(str(boxes)))
            self.ui.tableWidget_waypoints.setItem(row, 5, QTableWidgetItem(str(time)))
            self.ui.tableWidget_waypoints.setItem(row, 6, QTableWidgetItem(eta_str))

        def format_eta(point):
            if 'eta' in point:
                minutes = int(point['eta'])
                if minutes == 0:
                    return "0 хв (Старт)"
                hours = minutes // 60
                mins = minutes % 60
                if hours > 0:
                    return f"{hours} год {mins} хв"
                return f"{mins} хв"
            return "-"

        if self.points.start:
            add_row("СТАРТ", self.points.start['address'], self.points.start['coord'][0], self.points.start['coord'][1],
                    0, 0, format_eta(self.points.start))
            row += 1

        for idx, wp in enumerate(self.points.waypoints):
            pri = wp.get('priority', 3)
            time_str = f"{wp['time']} (+10)"
            add_row(f"Точка {idx + 1} (Пр:{pri})", wp['address'], wp['coord'][0], wp['coord'][1], wp['boxes'],
                    time_str, format_eta(wp))
            row += 1

        if self.points.finish:
            add_row("ФІНІШ", self.points.finish['address'], self.points.finish['coord'][0],
                    self.points.finish['coord'][1], 0, 0, format_eta(self.points.finish))

    def update_calculation_results(self, dist_km, driving_time_min, loading_time_min, exec_time_ms, mem_used_kb):
        self.ui.tableWidget_calculation.setRowCount(0)
        total_time = driving_time_min + loading_time_min
        results = [
            ("Загальна відстань", f"{dist_km:.2f} км"),
            ("Час у дорозі (їзда)", f"{driving_time_min:.0f} хв"),
            ("Час розвантаження (+затримки)", f"{loading_time_min:.0f} хв"),
            ("Орієнтовний заг. час", f"{total_time:.0f} хв"),
            ("Час роботи алгоритму", f"{exec_time_ms:.2f} мс"),
            ("Використано пам'яті", f"{mem_used_kb:.2f} KB")
        ]

        for row, (param, value) in enumerate(results):
            self.ui.tableWidget_calculation.insertRow(row)
            self.ui.tableWidget_calculation.setItem(row, 0, QTableWidgetItem(param))
            self.ui.tableWidget_calculation.setItem(row, 1, QTableWidgetItem(value))

    def update_map_view(self, route=None, route_color="#FFFF00"):
        html_content = MapRenderer.generate_map_html(self.points, route_coords=route, route_color=route_color)
        self.web_view.setHtml(html_content)
        self.web_view.setFocus()

    def save_sf_point(self, mode, data):
        if mode == 'start':
            self.points.set_start(data)
        elif mode == 'finish':
            self.points.set_finish(data)
        self.last_route = None
        self.ui.tableWidget_calculation.setRowCount(0)
        self.update_map_view()
        self.update_table_view()
        self.record_state()

    def open_new_waypoint(self):
        self.wp_window.clear_fields()
        self.wp_window.show()

    def save_waypoint(self, data, edit_index=None):
        if edit_index is not None:
            self.points.waypoints[edit_index] = data
        else:
            self.points.add_waypoint(data)

        if self.points.start and 'eta' in self.points.start:
            del self.points.start['eta']
        if self.points.finish and 'eta' in self.points.finish:
            del self.points.finish['eta']
        for wp in self.points.waypoints:
            if 'eta' in wp:
                del wp['eta']

        self.last_route = None
        self.ui.tableWidget_calculation.setRowCount(0)
        self.update_map_view()
        self.update_table_view()
        self.record_state()

    def get_selected_point_info(self):
        row = self.ui.tableWidget_waypoints.currentRow()
        if row < 0:
            return None, None

        item = self.ui.tableWidget_waypoints.item(row, 0)
        if not item:
            return None, None

        return row, item.text()

    def delete_selected_point(self):
        row, p_type = self.get_selected_point_info()
        if p_type is None:
            QMessageBox.warning(self, "Увага", "Виберіть точку (клітинку) в таблиці для видалення.")
            return

        reply = QMessageBox.question(self, 'Підтвердження', f'Ви впевнені, що хочете видалити: "{p_type}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if p_type == "СТАРТ":
                self.points.start = None
            elif p_type == "ФІНІШ":
                self.points.finish = None
            elif p_type.startswith("Точка"):
                try:
                    idx = int(p_type.split(' ')[1]) - 1
                    del self.points.waypoints[idx]
                except (IndexError, ValueError):
                    pass

            self.last_route = None
            self.ui.tableWidget_calculation.setRowCount(0)
            self.update_table_view()
            self.update_map_view()
            self.record_state()

    def edit_selected_point(self):
        row, p_type = self.get_selected_point_info()
        if p_type is None:
            QMessageBox.warning(self, "Увага", "Виберіть точку (клітинку) в таблиці для редагування.")
            return

        if p_type.startswith("Точка"):
            try:
                idx = int(p_type.split(' ')[1]) - 1
                wp_data = self.points.waypoints[idx]

                self.wp_window.clear_fields()
                self.wp_window.load_data(wp_data, idx)
                self.wp_window.setWindowTitle(f"Редагування: {p_type}")
                self.wp_window.show()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося відкрити точку для редагування:\n{e}")
        else:
            QMessageBox.information(self, "Інфо", "Редагувати замовлення можна лише для проміжних маршрутних точок.")

    def calculate_and_draw(self):
        if not self.points.start or not self.points.finish:
            QMessageBox.warning(self, "Увага", "Для обчислення маршруту задайте і СТАРТ, і ФІНІШ.")
            return

        start_pt = self.points.start
        finish_pt = self.points.finish
        start_coord = start_pt['coord']
        finish_coord = finish_pt['coord']

        pts_hash = self.get_points_hash()
        if pts_hash != self.current_points_hash:
            if self.current_points_hash is not None:
                QMessageBox.information(self, "Оновлення",
                                        "Точки маршруту було змінено. Результати минулих маршрутів для графіків очищено.")
            self.current_points_hash = pts_hash
            self.algo_results.clear()

        self.ui.pushButton_calculate_route.setText("Обчислення...")
        self.ui.pushButton_calculate_route.setEnabled(False)
        QApplication.processEvents()

        tracemalloc.start()
        start_time = time.time()

        selected_method = self.ui.comboBox_search_method.currentText()
        route_color = "#FFFF00"

        rout_type_text = self.ui.comboBox_rout_type.currentText()
        if "1." in rout_type_text:
            mode = 1
        elif "2." in rout_type_text:
            mode = 2
        elif "3." in rout_type_text:
            mode = 3
        else:
            mode = 4

        if self.points.waypoints:
            if selected_method == "A* (А-зірка)":
                sorted_waypoints = self.router.a_star_sort_waypoints(start_coord, finish_coord, self.points.waypoints,
                                                                     mode)
                route_color = "#FFFF00"
            elif selected_method == "Алгоритм Дейкстри":
                sorted_waypoints = self.router.dijkstra_sort_waypoints(start_coord, finish_coord, self.points.waypoints,
                                                                       mode)
                route_color = "#0000FF"
            elif selected_method == "Мурашиний алгоритм":
                sorted_waypoints = self.router.aco_sort_waypoints(start_coord, finish_coord, self.points.waypoints,
                                                                  mode)
                route_color = "#FF0000"
            else:
                sorted_waypoints = self.router.a_star_sort_waypoints(start_coord, finish_coord, self.points.waypoints,
                                                                     mode)

            self.points.waypoints = sorted_waypoints
        else:
            sorted_waypoints = []

        all_coords = [start_coord] + [wp['coord'] for wp in sorted_waypoints] + [finish_coord]

        road_route, distance_m, duration_sec, legs_durations = self.router.get_road_route(all_coords)

        current_eta = 0.0
        start_pt['eta'] = current_eta

        for i in range(len(self.points.waypoints)):

            if legs_durations and i < len(legs_durations):
                drive_time = legs_durations[i] / 60.0
            else:
                dist = geodesic(all_coords[i], all_coords[i + 1]).meters
                drive_time = (dist / 30000.0) * 60.0

            current_eta += drive_time
            self.points.waypoints[i]['eta'] = current_eta

            current_eta += self.points.waypoints[i].get('time', 0) + 10.0

        if legs_durations and len(legs_durations) == len(self.points.waypoints) + 1:
            drive_time = legs_durations[-1] / 60.0
        else:
            dist = geodesic(all_coords[-2], all_coords[-1]).meters
            drive_time = (dist / 30000.0) * 60.0

        current_eta += drive_time
        finish_pt['eta'] = current_eta

        self.update_table_view()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()

        if road_route:
            self.last_route = road_route
            self.last_route_color = route_color
            self.update_map_view(route=road_route, route_color=route_color)

            dist_km = distance_m / 1000
            driving_time_min = duration_sec / 60
            loading_time_min = sum(wp.get('time', 0) + 10 for wp in self.points.waypoints)

            exec_time_ms = (end_time - start_time) * 1000
            mem_used_kb = peak / 1024

            self.update_calculation_results(dist_km, driving_time_min, loading_time_min, exec_time_ms, mem_used_kb)

            self.algo_results[selected_method] = {
                "time": exec_time_ms,
                "mem": mem_used_kb
            }
        else:
            QMessageBox.warning(self, "Помилка маршрутизації",
                                "Не вдалося прокласти маршрут по дорогах. Перевірте з'єднання з інтернетом.")
            fallback_route = all_coords
            self.last_route = fallback_route
            self.last_route_color = route_color
            self.update_map_view(route=fallback_route, route_color=route_color)

        self.ui.pushButton_calculate_route.setText("Обчислити маршрут")
        self.ui.pushButton_calculate_route.setEnabled(True)
        self.record_state()

    def load_regular_deliveries(self):
        self.ui.pushButton_regular_deliveries.setText("Завантаження (бл. 15 сек)...")
        self.ui.pushButton_regular_deliveries.setEnabled(False)
        QApplication.processEvents()

        self.points.clear_all()
        self.last_route = None
        self.ui.tableWidget_calculation.setRowCount(0)
        geocoder = SmartGeocoder()

        base_address = "Літературна 11, Ірпінь, Київська область"
        try:
            base_res = geocoder.geocode(base_address)
            if base_res:
                base_lat, base_lon, base_resolved = base_res
                base_data = {'coord': [base_lat, base_lon], 'address': base_address, 'boxes': 0, 'time': 0}
                self.points.set_start(base_data)
                self.points.set_finish(base_data)
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося знайти базову адресу: {e}")

        addresses = [
            "проспект Павла Тичини, 1В, Київ",
            "проспект Володимира Івасюка, 46, Київ",
            "вулиця Самійла Кішки, 7, Київ",
            "проспект Петра Григоренка, 23, Київ",
            "бульвар Миколи Руденка, 14М, Київ",
            "вулиця Олеся Гончара, 96, Київ",
            "вулиця Олександра Мишуги, 4, Київ",
            "вулиця Борщагівська, 154А, Київ",
            "Дарницький бульвар, 8А, Київ",
            "Спортивна площа, 1А, Київ",
            "Берестейський проспект, 24, Київ",
            "проспект Володимира Івасюка, 27Б, Київ",
            "проспект Володимира Івасюка, 12, Київ",
            "вулиця Загорівська, 17-20, Київ",
            "вулиця Ярославська, 56А, Київ",
            "вулиця Глибочицька, 32Б, Київ",
            "вулиця Антоновича, 165, Київ",
            "Воскресенський проспект, 36, Київ",
            "вулиця Причальна, 14А, Київ",
        ]

        for addr in addresses:
            QApplication.processEvents()
            try:
                time.sleep(0.3)
                res = geocoder.geocode(addr)

                if res:
                    lat, lon, resolved_addr = res
                    boxes = random.randint(1, 10)
                    time_minutes = boxes * 2

                    priority = 3

                    raw_orders = {}

                    wp_data = {
                        'coord': [lat, lon],
                        'address': addr,
                        'boxes': boxes,
                        'time': time_minutes,
                        'priority': priority,
                        'raw_orders': raw_orders
                    }
                    self.points.add_waypoint(wp_data)
                else:
                    print(f"Адресу не знайдено: {addr}")
            except Exception as e:
                print(f"Помилка з'єднання для адреси {addr}: {e}")

        self.update_map_view()
        self.update_table_view()
        self.ui.pushButton_regular_deliveries.setText("Регулярні доставки")
        self.ui.pushButton_regular_deliveries.setEnabled(True)
        self.record_state()

    def add_imported_points(self, points_list: list[dict]):
        for wp in points_list:
            self.points.add_waypoint(wp)
        self.last_route = None
        self.ui.tableWidget_calculation.setRowCount(0)
        self.update_map_view()
        self.update_table_view()
        self.record_state()

    def closeEvent(self, event):
        try:
            self.history.clear()
            self.points.clear_all()
            self.algo_results.clear()
            self.last_route = None
            if hasattr(self, 'sf_window') and self.sf_window:
                self.sf_window.close()
            if hasattr(self, 'wp_window') and self.wp_window:
                self.wp_window.close()
            if hasattr(self, 'points_reader_window') and self.points_reader_window:
                self.points_reader_window.close()
            if hasattr(self, 'mem_window') and self.mem_window:
                self.mem_window.close()
            if hasattr(self, 'time_window') and self.time_window:
                self.time_window.close()
            gc.collect()
        except Exception as e:
            print(f"Помилка при очищенні ресурсів: {e}")
        event.accept()

    def get_points_hash(self):
        if not self.points.start or not self.points.finish:
            return None

        data = f"S:{self.points.start['coord']}_F:{self.points.finish['coord']}"


        wp_signatures = []
        for wp in self.points.waypoints:
            wp_signatures.append((wp['coord'][0], wp['coord'][1], wp.get('boxes', 0), wp.get('priority', 3)))

        wp_signatures.sort()


        for sig in wp_signatures:
            data += f"_W:{sig}"

        return hashlib.md5(data.encode()).hexdigest()

    def show_analytics_graphs(self):

        required_algos = ["A* (А-зірка)", "Алгоритм Дейкстри", "Мурашиний алгоритм"]
        missing = [algo for algo in required_algos if algo not in self.algo_results]

        if missing:
            msg = "Для побудови графіків необхідно обчислити маршрут для поточних точок усіма трьома алгоритмами.\n\nЗалишилось виконати:\n- " + "\n- ".join(
                missing)
            QMessageBox.warning(self, "Недостатньо даних", msg)
            return

        # ---------------------------------------------------------
        # ГРАФІК 1: Стовпчаста діаграма споживання пам'яті
        # ---------------------------------------------------------
        self.mem_window = QDialog(self)
        self.mem_window.setWindowTitle("Споживання оперативної пам'яті (Фіксована кількість замовлень)")
        self.mem_window.resize(650, 450)
        self.mem_window.setMinimumSize(650, 450)
        layout1 = QVBoxLayout(self.mem_window)

        fig1 = Figure(figsize=(6, 4))
        canvas1 = FigureCanvas(fig1)
        layout1.addWidget(canvas1)
        ax1 = fig1.add_subplot(111)

        algos = list(self.algo_results.keys())
        mems = [self.algo_results[a]["mem"] for a in algos]
        colors = ['#FFC107', '#007BFF', '#DC3545']

        bars = ax1.bar(algos, mems, color=colors)
        ax1.set_ylabel("Пам'ять (KB)")
        ax1.set_title("Споживання оперативної пам'яті різними алгоритмами")


        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, yval + (max(mems) * 0.02), f'{yval:.1f} KB', ha='center',
                     va='bottom', fontweight='bold')

        fig1.tight_layout()
        self.mem_window.show()

        # ---------------------------------------------------------
        # ГРАФІК 2: Залежність часу від кількості вузлів
        # ---------------------------------------------------------
        self.time_window = QDialog(self)
        self.time_window.setWindowTitle("Залежність часу виконання від кількості точок")
        self.time_window.resize(700, 500)
        self.time_window.setMinimumSize(700, 500)
        layout2 = QVBoxLayout(self.time_window)

        fig2 = Figure(figsize=(6, 4))
        canvas2 = FigureCanvas(fig2)
        layout2.addWidget(canvas2)
        ax2 = fig2.add_subplot(111)

        num_points = len(self.points.waypoints)
        if num_points == 0 or not self.points.start or not self.points.finish:
            ax2.text(0.5, 0.5, "Немає достатньо точок для побудови графіка", ha='center', va='center', fontsize=12)
        else:
            x_vals = list(range(1, num_points + 1))
            times_astar, times_dijkstra, times_aco = [], [], []
            start_coord = self.points.start['coord']
            finish_coord = self.points.finish['coord']


            for i in x_vals:
                subset = self.points.waypoints[:i]

                t0 = time.time()
                self.router.a_star_sort_waypoints(start_coord, finish_coord, subset)
                times_astar.append((time.time() - t0) * 1000)

                t0 = time.time()
                self.router.dijkstra_sort_waypoints(start_coord, finish_coord, subset)
                times_dijkstra.append((time.time() - t0) * 1000)

                t0 = time.time()
                self.router.aco_sort_waypoints(start_coord, finish_coord, subset)
                times_aco.append((time.time() - t0) * 1000)

            ax2.plot(x_vals, times_astar, marker='o', label="A* (А-зірка)", color='#FFC107', linewidth=2)
            ax2.plot(x_vals, times_dijkstra, marker='s', label="Алгоритм Дейкстри", color='#007BFF', linewidth=2)
            ax2.plot(x_vals, times_aco, marker='^', label="Мурашиний алгоритм", color='#DC3545', linewidth=2)

            ax2.set_xlabel("Кількість проміжних точок (вузлів)")
            ax2.set_ylabel("Час виконання (мс)")
            ax2.set_title("Часова складність: Залежність часу від масштабу графа")
            ax2.legend()
            ax2.grid(True, linestyle='--', alpha=0.6)

        fig2.tight_layout()
        self.time_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RouteOptimizerApp()
    window.show()
    sys.exit(app.exec())