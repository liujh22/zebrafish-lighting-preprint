getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(cowplot)
library(ggplot2)
library(stats)
library(ggpmisc)
library(MASS)

# Input#ggplot2 Input
prebout_data <- read.csv("Bout_data_preprocessed_SD_removed.csv")
prebout_data <- prebout_data[, c("pitch_initial", "angvel_initial_phase", "label")]
postbout_data <- read.csv("IBI_timeseries_data_preprocessed_SD_removed.csv")

####################
# Keep dd_day only #
####################
# Only keep label = "dd_day"/"ld_day" 
postbout_data <- postbout_data %>%
  filter(label == "dd_day")

prebout_data <- prebout_data %>%
  filter(label == "dd_day")

####################
# Set range for parameters
# pitch (-15,30)
# angvel (-10,10)
####################
postbout_data <- subset(postbout_data, ang >= -15 & ang <= 30 & angVel >= -10 & angVel <= 10)
prebout_data <- subset(prebout_data, pitch_initial >= -15 & pitch_initial <= 30 & angvel_initial_phase >= -10 & angvel_initial_phase <= 10)

# Calculate Probability Matrix
numBins <- 8

###################
# Pre Bout Matrix #
###################

# 计算俯仰角度和角速度的分位数边界
PitchEdges <- quantile(prebout_data$pitch_initial, probs = seq(0, 1, length.out = numBins + 1))
AVedges <- quantile(prebout_data$angvel_initial_phase, probs = seq(0, 1, length.out = numBins + 1))

# 初始化 ProbPreBout 矩阵
ProbPreBout <- matrix(0, nrow = length(PitchEdges) - 1, ncol = length(AVedges) - 1)

# 计算 ProbPreBout 矩阵
for (PitchInd in 1:(length(PitchEdges) - 1)) {
  PitchHit <- which(prebout_data$pitch_initial >= PitchEdges[PitchInd] & prebout_data$pitch_initial < PitchEdges[PitchInd + 1])
  for (AVind in 1:(length(AVedges) - 1)) {
    AVhit <- which(prebout_data$angvel_initial_phase >= AVedges[AVind] & prebout_data$angvel_initial_phase < AVedges[AVind + 1])
    ProbPreBout[PitchInd, AVind] <- length(intersect(PitchHit, AVhit)) / length(prebout_data$pitch_initial)
  }
}

####################
# Post Bout Matrix #
####################
# 计算俯仰角度和角速度的分位数边界
PitchEdges <- quantile(postbout_data$ang, probs = seq(0, 1, length.out = numBins + 1))
AVedges <- quantile(postbout_data$angVel, probs = seq(0, 1, length.out = numBins + 1))

# 初始化 ProbPostBout 矩阵
ProbPostBout <- matrix(0, nrow = length(PitchEdges) - 1, ncol = length(AVedges) - 1)

# 计算 ProbPostBout 矩阵
for (PitchInd in 1:(length(PitchEdges) - 1)) {
  PitchHit <- which(postbout_data$ang >= PitchEdges[PitchInd] & postbout_data$ang < PitchEdges[PitchInd + 1])
  for (AVind in 1:(length(AVedges) - 1)) {
    AVhit <- which(postbout_data$angVel >= AVedges[AVind] & postbout_data$angVel < AVedges[AVind + 1])
    ProbPostBout[PitchInd, AVind] <- length(intersect(PitchHit, AVhit)) / length(postbout_data$ang)
  }
}


####################
# Final Matrix #####
####################
# 初始化 BoutProbability 矩阵
BoutProbability <- matrix(0, nrow = length(PitchEdges) - 1, ncol = length(AVedges) - 1)

# 计算 BoutProbability 矩阵
for (PitchInd in 1:(length(PitchEdges) - 1)) {
  for (AVind in 1:(length(AVedges) - 1)) {
    if (ProbPostBout[PitchInd, AVind] != 0) {  # 防止除以零
      BoutProbability[PitchInd, AVind] <- ProbPreBout[PitchInd, AVind] / ProbPostBout[PitchInd, AVind]
    } else {
      BoutProbability[PitchInd, AVind] <- NA  # 如果 ProbPostBout 为零，则设为 NA
    }
  }
}


####
# Visualize 
####
# 转换矩阵为数据框
BoutProb_df <- as.data.frame(as.table(ProbPreBout))

# 为了更好地解释，将列重命名
colnames(BoutProb_df) <- c("PitchBin", "AVBin", "Probability")

ggplot(BoutProb_df, aes(x = PitchBin, y = AVBin, fill = Probability)) +
  geom_tile() + 
  scale_fill_gradientn(colors = c("blue", "green", "red"), na.value = "grey50") +
  labs(title = "Bout Probability Heatmap",
       x = "Pitch Bins",
       y = "Angular Velocity Bins",
       fill = "Probability") +
  theme_minimal()
