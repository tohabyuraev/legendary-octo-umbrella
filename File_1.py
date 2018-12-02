import numpy as np
from Modul_1 import *


class EulerianGrid(object):
    def __init__(self, init_data):
        self.buf = 0
        self.tau = 0
        self.R = init_data['R']
        self.k = init_data['k']
        self.kurant = init_data['Ku']
        self.num_coor = init_data['num_coor']

        self.press_cell = np.full(init_data['num_coor'], init_data['press'])
        self.ro_cell = np.full(init_data['num_coor'], init_data['ro'])
        self.v_cell = np.full(init_data['num_coor'], 0.0)
        self.energy_cell = np.full(init_data['num_coor'],
                                   init_data['press'] / (init_data['k'] - 1) / init_data['ro'])
        self.c_cell = np.full(init_data['num_coor'], np.sqrt(init_data['k'] * init_data['press'] / init_data['ro']))
        # Для расчета Маха на интерфейсе
        self.mah_cell_m = np.full(init_data['num_coor'], 0.0)
        self.mah_cell_p = np.full(init_data['num_coor'], 0.0)
        # Для расчета потока f (Векторы Ф )
        self.ff_param_m = np.array([np.full(init_data['num_coor'], 0.0), np.full(init_data['num_coor'], 0.0),
                                   np.full(init_data['num_coor'], 0.0)])
        self.ff_param_p = np.array([np.full(init_data['num_coor'], 0.0), np.full(init_data['num_coor'], 0.0),
                                   np.full(init_data['num_coor'], 0.0)])

        # Первая ячейка является нулевой и их 101
        # Границы располагаются справа от нулевой ячейки и их 100

        self.mah_interface = np.full(init_data['num_coor'], 0.0)
        self.c_interface = np.full(init_data['num_coor'], 0.0)
        # self.x_interface = np.linspace(0, init_data['Lo'], init_data['num_coor'])
        self.x_interface = np.full(init_data['num_coor'], 0.0)
        self.press_interface = np.full(init_data['num_coor'], 0.0)
        self.v_interface = np.full(init_data['num_coor'], 0.0)

        self.f_param = np.array([self.ro_cell * self.v_cell, self.press_cell + self.ro_cell * (self.v_cell ** 2),
                                self.v_cell * self.ro_cell * ((self.energy_cell + (self.v_cell ** 2) / 2) +
                                                              self.press_cell / self.ro_cell)])
        self.q_param = np.array([self.ro_cell, self.ro_cell * self.v_cell, self.ro_cell *
                                (self.energy_cell + (self.v_cell ** 2) / 2)])

    def get_q(self, x_interface_prev):
        self.buf = coef_stretch(self.x_interface[0], self.x_interface[1], x_interface_prev[0], x_interface_prev[1])
        # В переменную buf записаны [0] коэффициент растяжения и [1] расстояние между границами на пред шаге
        self.q_param[0] = self.buf[0] * (self.q_param[0] - self.tau / self.buf[1] * (np.roll(self.q_param[0], -1) -
                                                                                     self.q_param[0]))
        self.q_param[1] = self.buf[0] * (self.q_param[1] - self.tau / self.buf[1] * (np.roll(self.q_param[1], -1) -
                                                                                     self.q_param[1]))
        self.q_param[2] = self.buf[0] * (self.q_param[2] - self.tau / self.buf[1] * (np.roll(self.q_param[2], -1) -
                                                                                     self.q_param[2]))
        self.ro_cell = self.q_param[0]
        # Плотность при пересчете получается много отрицательной?
        self.v_cell = self.q_param[1] / self.ro_cell
        self.energy_cell = self.q_param[2] / self.q_param[0] - (self.v_cell ** 2) / 2
        self.press_cell = self.ro_cell * self.energy_cell * (self.k - 1)
        self.c_cell = np.sqrt(self.k * self.press_cell / self.ro_cell)

    def get_f(self):
        # Функция возможно работает правильно
        # (self.ff_param_p[0] - self.ff_param_m[0]) разность равняется 0, а это не хорошо
        self.f_param[0] = 0.5 * self.c_interface * (self.mah_interface *
                                                    (self.ff_param_p[0] + self.ff_param_m[0]) -
                                                    abs(self.mah_interface) *
                                                    (self.ff_param_p[0] - self.ff_param_m[0]))
        self.f_param[1] = 0.5 * self.c_interface * (self.mah_interface *
                                                    (self.ff_param_p[1] + self.ff_param_m[1]) -
                                                    abs(self.mah_interface) *
                                                    (self.ff_param_p[1] - self.ff_param_m[1])) + self.press_interface
        self.f_param[2] = 0.5 * self.c_interface * (self.mah_interface *
                                                    (self.ff_param_p[2] + self.ff_param_m[2]) -
                                                    abs(self.mah_interface) *
                                                    (self.ff_param_p[2] - self.ff_param_m
                                                     [2])) + self.press_interface * self.v_interface

    def get_ff(self, str):
        # Функция работает возможно правильно (по формуле сходится)
        if str == 'mines':
            for i in range(self.num_coor - 2):
                self.ff_param_m[0][i] = self.ro_cell[i]
                self.ff_param_m[1][i] = self.ro_cell[i] * self.v_cell[i]
                self.ff_param_m[2][i] = self.ro_cell[i] * (self.energy_cell[i] + (self.v_cell[i] ** 2) / 2 +
                                                           self.press_cell[i] / self.ro_cell[i])
        if str == 'plus':
            for i in range(self.num_coor - 2):
                self.ff_param_m[0][i] = self.ro_cell[i + 1]
                self.ff_param_m[1][i] = self.ro_cell[i + 1] * self.v_cell[i + 1]
                self.ff_param_m[2][i] = self.ro_cell[i + 1] * (self.energy_cell[i + 1] + (self.v_cell[i + 1] ** 2) / 2 +
                                                               self.press_cell[i + 1] / self.ro_cell[i + 1])

    def get_c_interface(self):
        # Функция работает правильно
        for i in range(self.num_coor - 1):
            self.c_interface[i] = (self.c_cell[i + 1] + self.c_cell[i]) / 2

    def get_mah_m(self):
        # Функция работает возможно правильно (по формуле)
        for i in range(self.num_coor - 1):
            self.mah_cell_m[i] = (self.v_cell[i] - self.v_interface[i]) / self.c_interface[i]
        # print(self.mah_cell_m)

    def get_mah_p(self):
        # Функция работает возможно правильно (по формуле)
        for i in range(self.num_coor - 1):
            self.mah_cell_p[i] = (self.v_cell[i + 1] - self.v_interface[i]) / self.c_interface[i]

    def get_mah_interface(self):
        # Функция работает возможно правильно (по формуле)
        # self.mah_cell_m = np.full(init_data['num_coor'], 0.0)
        # self.mah_cell_p = np.full(init_data['num_coor'], 0.0)
        # Значения справа и слева противоположны по знаку и не равны 0
        # print(fetta(self.mah_cell_p[98], 'plus'))
        for i in range(self.num_coor - 1):
            self.mah_interface[i] = fetta(self.mah_cell_m[i], 'plus') + fetta(self.mah_cell_p[i], 'mines')

    def get_press_interface(self):
        # Функция работает возможно правильно (по формуле)
        for i in range(self.num_coor - 1):
            self.press_interface[i] = getta(self.mah_cell_m[i], 'plus') * self.press_cell[i] + \
                               getta(self.mah_cell_p[i], 'mines') * self.press_cell[i+1]

    def get_tau(self):
        # Функция работает правильно
        buf = []
        for i in range(self.num_coor - 2):
            self.buf = (self.x_interface[i+1] - self.x_interface[i]) / (abs(self.v_cell[i + 1]) + self.c_cell[i + 1])
            buf.append(self.buf)
        self.buf = min(buf)
        self.tau = self.kurant * self.buf

    def border(self):
        # Функция работает возможно правильно
        self.q_param[1][0] = -self.q_param[1][1]
        self.q_param[1][self.num_coor - 1] = -self.q_param[1][self.num_coor - 2] + self.q_param[0][self.num_coor - 2] \
            * self.v_interface[self.num_coor - 2]

    def x_recalculation(self, long):
        # Функция работает правильно
        self.buf = np.linspace(0, long, init_data['num_coor'] - 1)
        for i in range(self.num_coor - 1):
            self.x_interface[i] = self.buf[i]
        self.x_interface[self.num_coor - 1] = 1


layer = EulerianGrid(init_data)
all_time_arr = []
all_speed_arr = []
all_press_arr = []
layer.x_recalculation(init_data['Lo'])

while layer.x_interface[layer.num_coor - 2] <= init_data['L']:
    layer.get_tau()
    layer.border()
    prev_x_interface = layer.x_interface  # Для расчета q
    answer = sp_cr(layer.press_cell[layer.num_coor - 2], init_data['mass'],
                   layer.v_interface[layer.num_coor - 2], layer.x_interface[layer.num_coor - 2], layer.tau)
    # answer возвращает скорость правой границы и приращение координаты
    # Пересчет скоростей и перемещений границ работает правильно)
    layer.x_recalculation(answer[1])
    layer.v_interface[layer.num_coor - 2] = answer[0]
    k_line = layer.v_interface[layer.num_coor - 2] / answer[1]
    layer.v_interface = k_line * layer.x_interface

    get_all_value(layer.tau, all_time_arr, 'time')
    get_all_value(layer.v_interface[len(layer.v_interface) - 1], all_speed_arr, 'speed')
    get_all_value(layer.press_cell[len(layer.press_interface) - 1], all_press_arr, 'press')

    layer.get_c_interface()
    layer.get_mah_m()
    layer.get_mah_p()
    layer.get_mah_interface()
    layer.get_press_interface()
    layer.get_ff('mines')
    layer.get_ff('plus')
    layer.get_f()
    layer.get_q(prev_x_interface)

# print(None)
get_plot(all_time_arr, all_speed_arr, 'Время', 'Скорость')

