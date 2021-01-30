#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/21 21:37
# @Author  : LBZ

"""
功能：
1.将MCI软件生成的标定文件（.ACF文件转成.TXT格式），提取螺栓标定数据，并清洗数据
2.将处理好的数据拟合出拟合函数
3.利用拟合函数生成新的标定拟合数据
4.将新的标定拟合数据保存为.csv文件
"""

import pandas as pd
import tkinter
from tkinter import messagebox
import tkinter.filedialog as fd
import numpy as np
from pynverse import inversefunc


def openfile():
    print('*'*36, '二.开始查找文件', '*'*36)
    # 读取选中的文件绝对路径名称
    file_path = fd.askopenfilename(initialdir=r'C:\Users\dabinde\Desktop',
                                    filetypes=[('text file', '.txt')])
    print(file_path, '-', type(file_path))
    print('*'*36, '二.查找文件结束', '*'*36)
    return file_path


def data_processing(file_path_gl):
    print('*' * 36, '三.开始处理文件', '*' * 36)
    # 标定文件的存放绝对路径
    file_path = file_path_gl
    # 用来提取标定文件中指定行
    temp_list = [0, 1, 2, 3, 45, 46]
    # 创建一个字典，用来存放标定文件的前几行基础信息
    cal_infos = {}
    # 用来存放标定文件原始路径
    original_file_path = ''
    # 用来确定几根螺栓完成的标定文件
    bolt_number = 0
    # 确定标定方法是Interpolation还是PolyFit
    cal_method = ''
    # 用来存放标定文件每列的表头
    cal_columns = []
    # 存放标定文件拟合列的列名称
    fitting_columns = []
    # 存放标定文件拟合列的单位
    fitting_units = []
    # 存放出现异常的结果
    e = ''

    # 获得数据文本指定几行的基本信息，存入字典
    with open(file_path, 'r', encoding='gbk') as f:
        data = f.readlines()
        for i in range(len(data)):
            if i in temp_list:
                cal_infos[i] = (data[i].replace('\n', '')).split(';')
    # print(cal_infos)
    # print()

    # 将指定几行的信息处理清洗
    try:
        original_file_path = cal_infos[0][0].replace('File Name:', '')
        # print(original_file_path)

        bolt_number = int(cal_infos[2][0].replace('TotBolts=', ''))
        # print(bolt_number)

        cal_method = cal_infos[2][1].strip()
        # print(cal_method)

        for i in cal_infos[3]:
            if i is not '':
                cal_columns.append(i)
        # print(cal_columns)

        for i in cal_infos[temp_list[4]]:
            if i is not '':
                fitting_columns.append(i)
        # print(fitting_columns)

        for i in cal_infos[temp_list[5]]:
            if i is not '':
                fitting_units.append(i)
        # print(fitting_units)
    except Exception as exception:
        e = exception
        messagebox.showerror(title='错误', message=[e, '\n非标定文件，请重新运行程序并选择！'])
    finally:
        if e == '':
            pass
        else:
            print('*' * 36, '一.主程序已结束', '*' * 36)
            exit()

    # 使用pandas读取数据
    df = pd.read_csv(file_path, delimiter=';', encoding='gbk', header=3, usecols=cal_columns)  # , skiprows=(4,5))

    # 将单个螺栓数据存入df_bolts
    df_bolts = df[0:40].astype(float)

    # 将单个螺栓数据按从小到大排序成一列，存入df_merged
    df_merged = pd.DataFrame()
    df_temp = df_bolts
    # 列名相同，才能concat
    df_temp.columns = ['temp'] * 2 * bolt_number
    for i in range(bolt_number):
        df_merged = pd.concat([df_merged, df_temp.iloc[:, i * 2:(i * 2 + 2)]], axis=0, ignore_index=True)
    df_merged.columns = ['Load(kN)', 'Time(nSec)']
    df_merged.astype(float)
    df_merged.sort_values(by=df_merged.columns[1], ascending=False)

    # 将MCI计算出的拟合数据存入df_merged
    df_mci = df[42:82].iloc[:, 0:2]
    df_mci.columns = [fitting_columns[0] + '/' + fitting_units[0], fitting_columns[1] + '/' + fitting_units[1]]
    df_mci = pd.DataFrame.reset_index(df_mci).drop('index', axis=1).astype(float)
    print('*' * 36, '三.文件处理完成', '*' * 36)
    return df_bolts, df_merged, df_mci


def fitting_trace_1d(file_path_gl, df):
    print('*' * 36, '四.开始拟合数据', '*' * 36)
    df_merged = df
    # 一维拟合函数
    fitting_func_1D = np.polynomial.polynomial.Polynomial.fit(x=df_merged.iloc[:, 1], y=df_merged.iloc[:, 0], deg=1)
    # # 获得拟合函数
    # print(fitting_func_1D)
    # # print(type(fitting_func_1D.convert().coef))
    # # 获得系数数组，按照次幂由低到高排列
    # print(fitting_func_1D.convert().coef)
    # # 低次幂系数
    # print(fitting_func_1D.convert().coef[0])
    # # 高次幂系数
    # print(fitting_func_1D.convert().coef[1])
    # 通过拟合函数，获得拟合数据
    # 输入x即可得到y，如fitting_func_1D(0)=-40.51129316096433
    coeff = 100
    step_num = 40
    x_zero = inversefunc(fitting_func_1D, 0)
    y_zero = fitting_func_1D(x_zero)
    max_time = int((df_merged.loc[:, df_merged.columns[1]].max() // coeff + 1) * coeff * 2)
    step_length = int(max_time / step_num)
    x_time = pd.DataFrame(np.arange(x_zero, max_time, step_length))
    x_time.columns = ['Time(nSec)']
    x_time_adj = pd.DataFrame(x_time-x_zero)
    x_time_adj.columns = ['Time_adj(nSec)']
    y_load = fitting_func_1D(x_time)
    y_load.columns = ['Load(kN)']

    # 将x_time,y_load整合成DataFrame数据导出
    df_fitting_1D = pd.concat([y_load, x_time_adj, x_time], axis=1)    # fitting_func_1D.convert().coef
    file_path_save = file_path_gl.replace('.TXT', '-1D.csv')
    df_fitting_1D.to_csv(file_path_save)
    print('*' * 36, '四.拟合数据成功', '*' * 36)


def fitting_trace_2d(file_path_gl, df):
    print('*' * 36, '四.开始拟合数据', '*' * 36)
    df_merged = df
    # 二维拟合函数
    fitting_func_2D = np.polynomial.polynomial.Polynomial.fit(x=df_merged.iloc[:, 1], y=df_merged.iloc[:, 0], deg=2)

    coeff = 100
    step_num = 40
    x_zero = inversefunc(fitting_func_2D, 0)
    y_zero = fitting_func_2D(x_zero)
    max_time = int((df_merged.loc[:, df_merged.columns[1]].max() // coeff + 1) * coeff * 2)
    step_length = int(max_time / step_num)
    x_time = pd.DataFrame(np.arange(x_zero, max_time, step_length))
    x_time.columns = ['Time(nSec)']
    x_time_adj = pd.DataFrame(x_time-x_zero)
    x_time_adj.columns = ['Time_adj(nSec)']
    y_load = fitting_func_2D(x_time)
    y_load.columns = ['Load(kN)']

    # 将x_time,y_load整合成DataFrame数据导出
    df_fitting_2D = pd.concat([y_load, x_time_adj, x_time], axis=1)
    df_fitting_2D
    file_path_save = file_path_gl.replace('.TXT', '-2D.csv')
    df_fitting_2D.to_csv(file_path_save)
    print('*' * 36, '四.拟合数据成功', '*' * 36)


def fitting_trace_3d(file_path_gl, df):
    print('*' * 36, '四.开始拟合数据', '*' * 36)
    df_merged = df
    # 三维拟合函数
    fitting_func_3D = np.polynomial.polynomial.Polynomial.fit(x=df_merged.iloc[:, 1], y=df_merged.iloc[:, 0], deg=3)

    # 通过拟合函数，获得拟合数据
    coeff = 100
    step_num = 40
    x_zero = inversefunc(fitting_func_3D, 0)
    y_zero = fitting_func_3D(x_zero)
    max_time = int((df_merged.loc[:, df_merged.columns[1]].max() // coeff + 1) * coeff * 2)
    step_length = int(max_time / step_num)
    x_time = pd.DataFrame(np.arange(x_zero, max_time, step_length))
    x_time.columns = ['Time(nSec)']
    x_time_adj = pd.DataFrame(x_time-x_zero)
    x_time_adj.columns = ['Time_adj(nSec)']
    y_load = fitting_func_3D(x_time)
    y_load.columns = ['Load(kN)']

    # 将x_time,y_load整合成DataFrame数据导出
    df_fitting_3D = pd.concat([y_load, x_time_adj, x_time], axis=1)
    file_path_save = file_path_gl.replace('.TXT', '-3D.csv')
    df_fitting_3D.to_csv(file_path_save)
    print('*' * 36, '四.拟合数据成功', '*' * 36)


if __name__ == '__main__':
    print('*'*36, '一.已进入主程序', '*'*36)
    retry2 = None
    key1 = True
    key2 = True

    while key1:
        # 选择文件，得到文件的绝对路径
        file_path_gl = openfile()
        if file_path_gl == None or file_path_gl == '':
            retry = tkinter.messagebox.askretrycancel('提示！！！', '未选择文件，是否选择文件？')
            if retry == True:
                key1 = True
            else:
                print('*' * 36, '一.主程序已结束', '*' * 36)
                exit()
        else:
            key1 = False
            # print(file_path_gl)

    # 进入循环，首选选择拟合阶数，根据不同阶数，进行拟合
    while key2:
        choose_mode = input('请选择拟合阶数：\n' +
                            '\t一幂次拟合：输入数字1\n' +
                            '\t二幂次拟合：输入数字2\n' +
                            '\t三幂次拟合：输入数字3\n' +
                            '\t退出请按‘q’:\t')
        # 处理文件数据，返回处理好的数据（Tuple元组）
        dp = data_processing(file_path_gl)
        # print(dp[1])
        try:
            if choose_mode == 'q' or choose_mode == 'Q':
                key2 = False
            elif int(choose_mode) == 1:
                # dp = data_processing(file_path_gl)
                fitting_trace_1d(file_path_gl, dp[1])
            elif int(choose_mode) == 2:
                # dp = data_processing(file_path_gl)
                fitting_trace_2d(file_path_gl, dp[1])
            elif int(choose_mode) == 3:
                # dp = data_processing(file_path_gl)
                fitting_trace_3d(file_path_gl, dp[1])
            else:
                raise ValueError
        except Exception as e:
            retry2 = tkinter.messagebox.askretrycancel('提示！', [e, '是否重新输入？'])
        finally:
            if retry2 is True:
                key2 = True
                retry2 = None
            elif retry2 is False:
                key2 = False
                retry2 = None
            else:
                pass
    print('*' * 36, '一.主程序已结束', '*' * 36)
