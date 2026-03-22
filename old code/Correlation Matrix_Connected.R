# 加载必要的库
library(corrplot)
library(dplyr)

# 读取数据
rm(list=ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data <- read.csv("Connected_data_preprocessed_SD_removed.csv")

# exclude strings
data<- data %>% select(-bout_uid, -epoch_uid, -to_bout, -ztime, -cond1, -light, -expNum)

# 将 'label' 列转换为因子
data$label <- as.factor(data$label)

# Convert all columns into Abs
data <- data %>% mutate_if(is.numeric, abs)

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

# 计算label=dd_day和label=ld_day的相关系数矩阵
cor_matrix_dd_day <- calculate_cor_matrix(split_data[["dd_day"]], numeric_cols)
cor_matrix_ld_day <- calculate_cor_matrix(split_data[["ld_day"]], numeric_cols)

# 可视化相关系数矩阵和差异矩阵
plot_cor_matrix <- function(cor_matrix, label, title_suffix) {
  col1 <- colorRampPalette(c("red", "white", "blue"))
  
  par(mar = c(1, 1, 3, 1))  # 底部、左侧、顶部、右侧边距
  par(oma = c(0, 0, 2, 0))  # 外部边距
  
  corrplot(cor_matrix, method = "color", col = col1(20), cl.length = 21, order = "AOE",
           addCoef.col = NULL, tl.col = "black", tl.pos = "lt", number.cex = 0.5, tl.cex = 0.5)
  
  title(main = paste("Correlation Matrix - Label:", label, title_suffix), outer = TRUE, line = -1)
}

# 绘制相关系数矩阵和差异矩阵
plot_cor_matrix(cor_matrix_dd_day, "dd_day", "")
plot_cor_matrix(cor_matrix_ld_day, "ld_day", "")

# Calculate the difference matrix
diff_matrix <- cor_matrix_dd_day - cor_matrix_ld_day
plot_cor_matrix(diff_matrix, "Difference (dd_day - ld_day)", "")
