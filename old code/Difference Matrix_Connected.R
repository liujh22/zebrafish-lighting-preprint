# 加载必要的库
library(corrplot)

# 读取数据
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data <- read.csv("PCA_preprocessed_connected.csv")

# 将 'label' 列转换为因子
data$label <- as.factor(data$label)

# 拆分数据
split_data <- split(data, data$label)

# 获取数值型列
numeric_cols <- names(data)[sapply(data, is.numeric)]

# 定义一个函数计算相关系数矩阵
calculate_cor_matrix <- function(df, numeric_cols) {
  abs_data <- abs(df[, numeric_cols])
  data_cor <- cor(abs_data)
  return(data_cor)
}

# 计算所有条件的相关系数矩阵
cor_matrices <- lapply(split_data, calculate_cor_matrix, numeric_cols)

# 定义条件名称
conditions <- names(split_data)

# 使用Fisher变换函数
fisher_transform <- function(r) {
  return(0.5 * log((1 + r) / (1 - r)))
}

# 将相关系数矩阵变换为z分数矩阵
z_matrices <- lapply(cor_matrices, function(mat) apply(mat, c(1, 2), fisher_transform))

# 定义一个函数可视化相关系数矩阵
plot_cor_matrix <- function(cor_matrix, label, title_suffix = "") {
  col1 <- colorRampPalette(c("red", "white", "blue"))
  
  par(mar = c(1, 1, 3, 1))  # 底部、左侧、顶部、右侧边距
  par(oma = c(0, 0, 2, 0))  # 外部边距
  
  corrplot(cor_matrix, method = "color", col = col1(20), cl.length = 21, order = "AOE",
           addCoef.col = NULL, tl.col = "black", tl.pos = "lt", number.cex = 0.5, tl.cex = 0.5)
  
  title(main = paste("Correlation Matrix - Label:", label, title_suffix), outer = TRUE, line = -1)
}

# 定义要对比的条件
lighting_effects <- list(c("dd_day", "ld_day"), c("ld_night", "ll_night"))
circadian_effects <- list(c("dd_day", "dd_night"), c("ll_day", "ll_night"))

# 可视化lighting effect
for (effect in lighting_effects) {
  condition1 <- effect[[1]]
  condition2 <- effect[[2]]
  
  # 查找条件的索引
  i <- which(conditions == condition1)
  j <- which(conditions == condition2)
  
  # 计算差异矩阵
  diff_matrix <- cor_matrices[[i]] - cor_matrices[[j]]
  
  # 可视化差异矩阵
  plot_cor_matrix(diff_matrix, paste(condition1, "vs", condition2), title_suffix = " (Lighting Effect)")
}

# 可视化circadian effect
for (effect in circadian_effects) {
  condition1 <- effect[[1]]
  condition2 <- effect[[2]]
  
  # 查找条件的索引
  i <- which(conditions == condition1)
  j <- which(conditions == condition2)
  
  # 计算差异矩阵
  diff_matrix <- cor_matrices[[i]] - cor_matrices[[j]]
  
  # 可视化差异矩阵
  plot_cor_matrix(diff_matrix, paste(condition1, "vs", condition2), title_suffix = " (Circadian Effect)")
}