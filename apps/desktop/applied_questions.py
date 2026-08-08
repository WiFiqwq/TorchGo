"""代码、Shape、排错、场景与进阶理解题。correct 为正确选项的零基索引。"""

import random

from deep_knowledge import DEEP_KNOWLEDGE
from pytorch_quiz import CATEGORY_TO_CHAPTER, CHAPTERS


def q(chapter, qid, qtype, difficulty, prompt, options, correct, explanation):
    return {
        "id": qid, "chapter": CHAPTERS[chapter - 1], "type": qtype,
        "difficulty": difficulty, "prompt": prompt, "options": options,
        "correct_index": correct, "explanation": explanation,
    }


APPLIED_QUESTIONS = [
    # 第1章
    q(1, "shape_001", "Shape题", "基础", "x = torch.randn(8, 3, 224, 224)，x.shape 是什么？", ["[8, 3, 224, 224]", "[3, 8, 224, 224]", "[8, 224, 224, 3]", "[8, 3, 50176]"], 0, "torch.randn 接收的参数就是新 Tensor 的各维尺寸。"),
    q(1, "shape_002", "代码题", "理解", "x.shape=[4,3,32,32]，执行 x = x.unsqueeze(1) 后 shape 是什么？", ["[4, 1, 3, 32, 32]", "[1, 4, 3, 32, 32]", "[4, 3, 1, 32, 32]", "[4, 3, 32, 32]"], 0, "unsqueeze(1) 在索引 1 的位置插入大小为 1 的新维度。"),
    q(1, "shape_003", "代码题", "理解", "x.shape=[2,3,10,20]，x.permute(0,2,3,1) 的输出 shape 是什么？", ["[2, 10, 20, 3]", "[2, 20, 10, 3]", "[3, 2, 10, 20]", "[2, 3, 20, 10]"], 0, "permute 按给出的维度索引顺序重新排列，得到 B、H、W、C。"),
    q(1, "debug_001", "排错题", "应用", "模型在 CUDA 上，而输入 images 在 CPU 上，最可能发生什么？", ["设备不一致错误", "自动把输入移到 CUDA", "只会降低速度但不报错", "模型自动移回 CPU"], 0, "同一次算子的参数和输入必须位于兼容设备，应把 images 移到模型所在设备。"),

    # 第2章
    q(2, "data_001", "场景题", "基础", "训练集与验证集的 shuffle 设置通常应当是什么？", ["训练 True，验证 False", "训练 False，验证 True", "二者都必须 True", "二者都必须 False"], 0, "训练集打乱可减少顺序偏差；验证集无需打乱，便于稳定复现。"),
    q(2, "data_002", "排错题", "理解", "CrossEntropyLoss 报错提示标签类型不正确，单标签多分类的 target 通常应使用什么 dtype？", ["torch.int64", "torch.float32", "torch.bool", "torch.float16"], 0, "CrossEntropyLoss 的类别索引 target 通常是 torch.long，也就是 int64。"),
    q(2, "data_003", "场景题", "理解", "不同样本的目标框数量不同，DataLoader 默认组 batch 失败，最合适的处理是什么？", ["自定义 collate_fn", "增大 batch_size", "开启 shuffle", "把 num_workers 设为 0"], 0, "默认堆叠要求形状一致；自定义 collate_fn 可把不同数量的标注保留为列表。"),
    q(2, "data_004", "排错题", "应用", "图像用 OpenCV 读取后直接按 ImageNet 的 RGB 均值归一化，问题最可能是什么？", ["BGR 与 RGB 通道顺序不匹配", "图像一定会变成灰度", "标签会自动改变", "batch 维度会消失"], 0, "OpenCV 默认 BGR，应先转换为 RGB 或按实际顺序处理。"),

    # 第3章
    q(3, "train_001", "流程题", "基础", "普通训练步骤的合理顺序是哪一个？", ["zero_grad → forward → loss → backward → step", "forward → step → loss → backward → zero_grad", "backward → forward → step → loss → zero_grad", "zero_grad → step → forward → backward → loss"], 0, "先清梯度，再前向计算 loss，随后反向计算梯度并更新参数。"),
    q(3, "train_002", "概念题", "理解", "调用 loss.backward() 后，模型参数是否已经更新？", ["没有，只计算并累积了梯度", "已经由 backward 自动更新", "只有 bias 被更新", "只有使用 SGD 时才更新"], 0, "参数更新由 optimizer.step() 完成，backward 只负责梯度。"),
    q(3, "train_003", "排错题", "理解", "忘记每个 batch 调用 zero_grad()，最直接的结果是什么？", ["不同 batch 的梯度不断累积", "模型自动进入 eval 模式", "DataLoader 停止打乱", "loss 自动变为零"], 0, "PyTorch 默认累积梯度，除非这是刻意的梯度累积，否则会改变更新结果。"),
    q(3, "train_004", "场景题", "应用", "训练 loss 持续下降，但验证 loss 开始上升，最可能说明什么？", ["模型正在过拟合", "模型一定欠拟合", "GPU 显存不足", "标签 dtype 错误"], 0, "训练集改善而验证集变差是典型过拟合信号。"),

    # 第4章
    q(4, "cnn_001", "Shape题", "基础", "输入 [8,3,224,224] 经过 Conv2d(3,32,3,stride=2,padding=1)，输出 shape 是什么？", ["[8,32,112,112]", "[8,3,112,112]", "[8,32,224,224]", "[32,8,112,112]"], 0, "输出通道为 32，stride=2 使 H、W 约减半。"),
    q(4, "cnn_002", "Shape题", "理解", "x1=[B,64,32,32]、x2=[B,128,32,32]，沿通道维 torch.cat 后 shape 是什么？", ["[B,192,32,32]", "[B,128,64,32]", "[B,64,32,32]", "[B,128,32,32]"], 0, "沿 C 维拼接时通道数相加，其他维度保持相同。"),
    q(4, "cnn_003", "计算题", "应用", "不考虑 bias，Conv2d(3,16,kernel_size=3) 有多少个可学习权重？", ["432", "144", "48", "1296"], 0, "权重形状为 [16,3,3,3]，元素数是 16×3×3×3=432。"),
    q(4, "cnn_004", "概念题", "理解", "BatchNorm 后切换 model.eval() 的主要影响是什么？", ["使用训练期间累计的运行均值和方差", "删除所有可学习参数", "停止全部梯度计算", "输出通道数减半"], 0, "eval 改变 BatchNorm 的统计方式，但不会自动关闭梯度。"),

    # 第5章
    q(5, "backbone_001", "概念题", "基础", "Backbone 越深的特征通常具有什么特点？", ["分辨率更低、语义更强", "分辨率更高、语义更弱", "通道一定更少", "只包含颜色信息"], 0, "深层特征通常经过下采样，空间更粗但语义表达更强。"),
    q(5, "backbone_002", "场景题", "理解", "细小车道线既需要定位细节又需要全局语义，最合适的思路是什么？", ["融合浅层与深层多尺度特征", "只使用最后一层特征", "删除所有下采样层", "只使用原始 RGB"], 0, "FPN、U-Net 等结构都通过多层特征融合兼顾细节和语义。"),
    q(5, "backbone_003", "概念题", "理解", "ResNet 中 y=F(x)+x 的主要价值是什么？", ["改善深层网络的信息和梯度传播", "把通道数必然翻倍", "把输入转换为概率", "替代损失函数"], 0, "残差路径提供更直接的信息与梯度通道。"),
    q(5, "backbone_004", "场景题", "应用", "移动端对速度和模型大小要求很高，优先考虑哪类 Backbone？", ["MobileNet", "VGG-19", "超宽 ResNet", "只用 Linear"], 0, "MobileNet 通过深度可分离卷积等技术减少计算和参数。"),

    # 第6章
    q(6, "trick_001", "场景题", "基础", "GPU 显存不足时，最直接且通常有效的措施是什么？", ["减小 batch_size", "增大输入分辨率", "增加模型通道", "关闭数据增强"], 0, "减小 batch 通常能直接降低激活占用，也可配合 AMP。"),
    q(6, "trick_002", "流程题", "理解", "AMP 训练中通常配合使用哪两个组件？", ["autocast 与 GradScaler", "DataLoader 与 Sampler", "Softmax 与 argmax", "eval 与 dropout"], 0, "autocast 选择计算精度，GradScaler 缩放梯度以降低下溢风险。"),
    q(6, "trick_003", "场景题", "理解", "类别极不平衡且大量样本很容易分类，哪种损失更适合强调困难样本？", ["Focal Loss", "普通 MSE", "只使用 L1", "取消 loss"], 0, "Focal Loss 会降低易分类样本贡献并聚焦困难样本。"),
    q(6, "trick_004", "排错题", "应用", "恢复训练时只加载模型权重，不加载 optimizer，最主要的影响是什么？", ["优化器动量等状态丢失", "模型结构自动删除", "数据集无法读取", "forward 不再执行"], 0, "可以继续训练，但 Adam 动量、学习率调度等状态无法无缝衔接。"),

    # 第7章
    q(7, "cls_001", "Shape题", "基础", "10类图像分类中，batch_size=32，分类器 logits 的典型 shape 是什么？", ["[32,10]", "[10,32]", "[32,3,224,224]", "[32,1]"], 0, "每个样本对应 10 个类别分数，因此是 [B,C]。"),
    q(7, "cls_002", "排错题", "理解", "使用 CrossEntropyLoss 前又手动对 logits 做 Softmax，为什么通常不推荐？", ["损失内部已包含稳定的 LogSoftmax 计算", "Softmax 会增加类别数", "Softmax 只能用于 CPU", "标签会变成图像"], 0, "直接传 logits 数值更稳定，也符合 CrossEntropyLoss 设计。"),
    q(7, "cls_003", "场景题", "理解", "一张图可同时包含“汽车、道路、行人”多个标签，应采用什么设置？", ["多标签分类 + BCEWithLogitsLoss", "单标签分类 + argmax 标签", "回归 + MSELoss", "语义分割 mask"], 0, "多个标签彼此不互斥，应独立预测每个标签概率。"),
    q(7, "cls_004", "场景题", "应用", "小数据集上使用 ImageNet 预训练 Backbone，较稳妥的起步方式是什么？", ["先训练新分类 Head，再逐步解冻微调", "立即随机删除全部权重", "只训练输入图片", "始终保持 model.eval()"], 0, "先保护预训练特征，再以较小学习率微调通常更稳定。"),

    # 第8章
    q(8, "seg_001", "Shape题", "基础", "4类语义分割、batch_size=8、标签大小 256×256，模型 logits 的典型 shape 是什么？", ["[8,4,256,256]", "[8,256,256,4]", "[4,8,256,256]", "[8,1,4]"], 0, "PyTorch 卷积网络通常输出 [B,C,H,W]。"),
    q(8, "seg_002", "排错题", "理解", "分割 logits 是 [B,C,64,64]，标签是 [B,256,256]，计算逐像素交叉熵前应先做什么？", ["把 logits 上采样到 256×256", "把 batch_size 改成 C", "对标签执行 Softmax", "删除类别维"], 0, "预测与标签的空间位置必须一一对应。"),
    q(8, "seg_003", "场景题", "理解", "背景占 98% 时只看 Pixel Accuracy 有什么风险？", ["即使漏掉前景，指标也可能很高", "指标一定等于零", "模型无法反向传播", "输出尺寸会翻倍"], 0, "类别极不平衡时应结合 IoU、Dice 等指标。"),
    q(8, "seg_004", "概念题", "应用", "U-Net 的 Skip Connection 为什么对边界定位有帮助？", ["把编码器高分辨率细节传给解码器", "自动生成更多训练标签", "把 loss 固定为零", "删除深层语义"], 0, "浅层细节可以补偿解码阶段因下采样丢失的位置信息。"),

    # 第9章
    q(9, "det_001", "计算题", "基础", "预测框与真实框完全重合时，IoU 等于多少？", ["1", "0", "0.5", "取决于类别数"], 0, "完全重合时交集与并集面积相等，因此 IoU=1。"),
    q(9, "det_002", "场景题", "理解", "同一辆车周围产生多个高度重叠的检测框，通常使用什么操作去重？", ["NMS", "BatchNorm", "RandomCrop", "GradScaler"], 0, "NMS 保留高置信度框并抑制与其高度重叠的重复框。"),
    q(9, "det_003", "概念题", "理解", "Anchor-free 检测器的主要特征是什么？", ["不依赖预先设计的候选框模板", "不需要训练数据", "只能检测一个类别", "不输出位置"], 0, "它通常直接预测中心点、边界距离或关键点。"),
    q(9, "lane_001", "场景题", "应用", "车道线非常细且前景像素很少，训练分割模型时重点关注什么？", ["类别不平衡与结构连续性", "只提高背景准确率", "把所有车道变成矩形框", "取消数据增强"], 0, "可结合类别权重、Dice/Focal 类损失以及连续性约束。"),

    # 第10章
    q(10, "vit_001", "计算题", "基础", "224×224 图像切成不重叠的 16×16 patch，不计 CLS token，共有多少个 patch？", ["196", "256", "224", "14"], 0, "每边 224/16=14，共 14×14=196 个 patch。"),
    q(10, "vit_002", "概念题", "理解", "Self-Attention 中真正被加权汇总的内容是哪一个？", ["Value", "Query", "Key", "位置索引"], 0, "Q 与 K 产生权重，权重再对 V 做加权求和。"),
    q(10, "vit_003", "场景题", "理解", "Swin Transformer 使用局部窗口注意力的主要目的是什么？", ["降低高分辨率图像上的注意力计算量", "彻底取消位置信息", "只处理文本", "让通道永远等于3"], 0, "注意力限制在窗口内可避免对全部 token 做昂贵的全局两两计算。"),
    q(10, "vit_004", "概念题", "应用", "DETR 中 Object Query 的作用是什么？", ["查询潜在目标并产生一组集合预测", "读取图像文件路径", "替代所有图像 patch", "计算数据增强概率"], 0, "每个 query 通过解码器关注图像特征并预测一个目标或空类别。"),
]


# 每章从进阶知识层生成 16 道“实践判断”题。选项来自同章真实实践提示，
# 因而比跨章节随机干扰更接近真实概念混淆。固定种子保证题库稳定。
_rng = random.Random(20260807)
for _chapter_index, _chapter in enumerate(CHAPTERS, 1):
    _entries = [item for item in DEEP_KNOWLEDGE if CATEGORY_TO_CHAPTER.get(item[1]) == _chapter]
    _selected = _rng.sample(_entries, min(16, len(_entries)))
    for _number, _entry in enumerate(_selected, 1):
        _distractor_pool = [item for item in _entries if item[0] != _entry[0]]
        _distractors = _rng.sample(_distractor_pool, 3)
        _options = [_entry[3]] + [item[3] for item in _distractors]
        _correct_text = _options[0]
        _rng.shuffle(_options)
        APPLIED_QUESTIONS.append(q(
            _chapter_index,
            f"advanced_{_chapter_index:02d}_{_number:02d}",
            "进阶理解题",
            "应用",
            f"在实际使用“{_entry[0]}”时，下列说法哪一项正确？",
            _options,
            _options.index(_correct_text),
            f"{_entry[0]}：{_entry[2]}。{_entry[3]}",
        ))
