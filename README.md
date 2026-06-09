# x3_mobile_control(ROS2版)

### 视频

[![项目演示视频](https://JustCoder1109.github.io/x3_mobile_control/X3_mobile.mp4)](https://JustCoder1109.github.io/x3_mobile_control/video.html)

点击上方封面可播放演示视频

### 程序运行平台

- 硬件：Rosmaster_X3 / Orin开发板
- 系统：jetpack / docker / ROS2
- 功能包、节点：hzt_mcnamu_mobile hzt_keyboard_control
- 程序路径：/root/hzt_ws/src/hzt_mcnamu_mobile/hzt_mcnamu_mobile/hzt_keyboard_control.py

### hzt_keyboard_control.py 代码简介

- 关键类和方法：

    TerminalReader：

        read_key：读取键盘按键
    HztKeyboardNode(Node) ：发布运动信息，控制小车移动

        run：主要流程，循环读取按键，发布运动信息
        handle_key：按键处理
        set_linear_state：设置直线速度
        set_angular_state：设置旋转速度
        clear_motion：刹车停止

### 程序流程图

```mermaid

graph TD
    Start([Start]) --> Init[初始化 ROS2 节点]
    Init --> Loop{循环读取键盘输入}
    Loop --> ReadKey["read_key(INPUT_TIMEOUT)"]
    ReadKey --> |有按键| CheckQuit{按键是否为 q / Ctrl-C / Ctrl-D ?}
    CheckQuit --> |是| Exit[结束程序]
    CheckQuit --> |否| Handle["调用 handle_key(key)"]
    Handle --> KeyType{按键类型}
    KeyType --> |w/s/a/d| SetLinear[设置 linear_state]
    KeyType --> |left/right| SetAngular[设置 angular_state]
    KeyType --> |其他| Ignore[忽略按键]
    SetLinear --> UpdateTime[更新 last_input_time]
    SetAngular --> UpdateTime
    Ignore --> Loop
    UpdateTime --> Publish[构建 Twist 并 publish]
    Publish --> Spin["rclpy.spin_once(timeout_sec=0)"]
    Spin --> Loop

    ReadKey --> |无按键| TimeoutCheck[检查是否超过 INPUT_TIMEOUT]
    TimeoutCheck --> |超过| Clear["clear_motion()"]
    Clear --> Publish
    TimeoutCheck --> |未超过| Publish

    Exit --> End([End])
```

### 流程说明

- 程序初始化 ROS2 节点 `HztKeyboardNode`
- 通过 `TerminalReader.read_key()` 非阻塞读取键盘输入
- 按键映射为线性/角速度状态，并发布 `geometry_msgs/Twist` 到 `/cmd_vel`
- 若超过超时未按键，则清空运动状态并发布静止指令
- 按 `q` 或 Ctrl-C/Ctrl-D 退出程序



