# 神经网络实现手写数字（二进制）识别
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
import matplotlib.pyplot as plt
import logging
import cv2  # 导入 OpenCV 用于摄像头操作
# 配置 TensorFlow 日志级别
logging.getLogger("tensorflow").setLevel(logging.ERROR)
tf.autograph.set_verbosity(0)

def load_data():
    print("正在加载 MNIST 数据集...")
    # 加载 MNIST 数据集
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    # 组合训练集和测试集以获取更多数据
    X_all = np.concatenate((x_train, x_test), axis=0)
    y_all = np.concatenate((y_train, y_test), axis=0)
    # 筛选出标签为 0 和 1 的样本
    indices = np.where((y_all == 0) | (y_all == 1))
    X = X_all[indices]
    y = y_all[indices]
    # 增加样本数量，使用所有可用的 0 和 1 数据，不再限制前1000个
    # 这样可以让模型见识更多样化的写法，提高泛化能力
    # X = X[:1000] 
    # y = y[:1000]
    # 预处理：归一化并调整大小
    X = X.astype(np.float32) / 255.0  # 归一化到 0-1
    X = np.expand_dims(X, axis=-1)    # 增加通道维度
    # 调整图像大小到 20x20
    X_resized = tf.image.resize(X, [20, 20]).numpy()
    # 展平为 (Num, 400)
    X_flat = X_resized.reshape(-1, 400)
    # y 已经是 (Num,)，调整为 (Num, 1)
    y = y.reshape(-1, 1)
    print(f"数据加载完成。X shape: {X_flat.shape}, y shape: {y.shape}")
    return X_flat, y
# 1. 加载数据
X, y = load_data()
# 2. 构建神经网络模型
# 改进点：
# 1. 增加每层的神经元数量 (25->64, 15->32)
# 2. 增加 Dropout 层防止过拟合
model = Sequential([
    tf.keras.Input(shape=(400,)),    
    Dense(64, activation='relu', name='layer1'),
    Dropout(0.2), # 随机丢弃 20% 神经元
    Dense(32, activation='relu', name='layer2'),
    Dropout(0.2),
    Dense(1, activation='sigmoid', name='output')
], name="my_model_improved")
model.summary()
# 3. 编译模型
model.compile(
    loss=tf.keras.losses.BinaryCrossentropy(),
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    metrics=['accuracy']
)
# 4. 训练模型
# 增加 epochs 次数 (20->50) 让模型训练更充分
print("开始训练模型...")
history = model.fit(
    X, y,
    epochs=50,
    batch_size=32, # 显式指定 batch_size
    validation_split=0.2, # 划分验证集监控过拟合
    verbose=1
)
# 5. 可视化训练过程
print("\n正在显示训练曲线... 请关闭图表窗口以继续进入摄像头识别模式。")
plt.plot(history.history['loss'], label='Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.plot(history.history['accuracy'], label='Accuracy')
plt.plot(history.history['val_accuracy'], label='Val Accuracy')
plt.title('Training History')
plt.xlabel('Epoch')
plt.legend()
plt.show()

def real_time_predict(model):
    print("\n" + "="*50)
    print("正在启动摄像头进行实时识别...")
    print("操作指南:")
    print("1. 请准备一张白纸，上面用粗黑色笔写上数字 0 或 1。")
    print("2. 确保光线充足，不要有阴影。")
    print("3. 按 'q' 键退出程序。")
    print("="*50 + "\n")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("错误: 无法打开摄像头，请检查设备连接。")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 获取画面中心
        height, width = frame.shape[:2]
        box_size = 200
        x1, y1 = (width - box_size) // 2, (height - box_size) // 2
        x2, y2 = x1 + box_size, y1 + box_size

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        roi = frame[y1:y2, x1:x2]
        # --- 增强预处理逻辑 ---
        # 1. 转灰度
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # 2. 高斯模糊去噪 (新加)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # 3. 自适应阈值二值化 (改进：替代固定阈值)
        # 这样能更好适应不同的光照条件
        # block_size=11, C=2
        thresh = cv2.adaptiveThreshold(blurred, 255,
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        # 4. 形态学操作：膨胀 (新加)
        # 让数字笔画变粗，连接断点，更接近 MNIST 风格
        kernel = np.ones((3,3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        # 5. 调整大小到 20x20
        resized = cv2.resize(dilated, (20, 20), interpolation=cv2.INTER_AREA)
        # 6. 归一化并展平
        input_data = resized.astype(np.float32) / 255.0
        input_data = input_data.reshape(1, 400)
        # 预测
        prediction = model.predict(input_data, verbose=0)
        score = prediction[0][0]
        # 判定结果 (增加置信度阈值)
        # 如果预测概率在 0.4~0.6 之间，认为不确定
        if score < 0.1:
            result_label = "0"
            conf = 1 - score
            color = (0, 255, 0)
        elif score > 0.9:
            result_label = "1"
            conf = score
            color = (0, 255, 0)
        else:
            result_label = "?"
            conf = 0.0
            color = (0, 0, 255) # 红色表示不确定
        # 显示结果
        cv2.putText(frame, f"Pred: {result_label}", (x1, y1 - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, f"Prob: {score:.4f}", (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        # 显示处理后的中间图，方便用户调整
        debug_view = cv2.resize(dilated, (100, 100), interpolation=cv2.INTER_NEAREST)
        frame[0:100, 0:100] = cv2.cvtColor(debug_view, cv2.COLOR_GRAY2BGR)
        cv2.putText(frame, "Processed", (5, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        cv2.imshow('Handwritten Digit Recognition (Press q to quit)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
# 启动摄像头识别
input("按回车键启动摄像头识别模式...")
real_time_predict(model)
