library(dplyr)
library(ggplot2)
library(ggpubr)
library(cowplot)
library(MASS)

rm(list = ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data <- read.csv("PCA_preprocessed_IBI.csv")

# 设定160个格子
numBins <- 160

# 区间为0到20，每个格子长0.125
edges <- seq(0, 20, length.out = numBins + 1)

# 四种情况
conditions <- list(
  light = data[data$light == "light", ],
  dark = data[data$light == "no light", ],
  day = data[data$ztime == "day", ],
  night = data[data$ztime == "night", ]
)

# 循环遍历每种情况并生成图表
plots <- list()
plots_bout <- list()
for (cond in names(conditions)) {
  IEI <- conditions[[cond]][conditions[[cond]]$propBoutIEI <= 20, ]$propBoutIEI
  boutrate <- 1/IEI
  # 把原始IEI 和 Bout rate 分布塞入这样的格子里
  targetIEIdist <- hist(IEI, breaks = edges, plot = FALSE)$counts
  target_bout_rate <- hist(boutrate, breaks = edges, plot = FALSE)$counts
  
  # 标准化
  targetIEIdist <- targetIEIdist / sum(targetIEIdist)
  target_bout_rate <- target_bout_rate/ sum(target_bout_rate)
  
  # 数据框用于绘图
  data_plot <- data.frame(x = IEI)
  data_plot_bout_rate <- data.frame(x = boutrate)
  
  # IEI
  p <- ggplot(data_plot, aes(x)) +
    geom_histogram(aes(y = ..density..), breaks = edges, color = "black", fill = "lightblue") +
    stat_function(fun = dnorm, args = list(mean = mean(data_plot$x), sd = sd(data_plot$x)), color = "red", size = 1) +
    ylim(0, 2) +
    xlim(0, 10) +
    labs(title = paste("Histogram with 160 bins -", cond),
         x = "IEI(s)",
         y = "Density") +
    theme_minimal()
  
  # Bout rate
  p2 <- ggplot(data_plot_bout_rate, aes(x)) +
    geom_histogram(aes(y = ..density..), breaks = edges, color = "black", fill = "lightblue") +
    stat_function(fun = dnorm, args = list(mean = mean(data_plot_bout_rate$x), sd = sd(data_plot_bout_rate$x)), color = "red", size = 1) +
    ylim(0, 2) +
    xlim(0, 10) +
    labs(title = paste("Histogram with 160 bins -", cond),
         x = "Bout Rate(Hz)",
         y = "Density") +
    theme_minimal()
  # 存储图表
  plots[[cond]] <- p
  plots_bout[[cond]] <- p2
}

# 使用 cowplot 包组合图表
plot_grid(plotlist = plots, ncol = 2)
plot_grid(plotlist = plots_bout, ncol = 2)
