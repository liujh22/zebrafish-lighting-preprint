# Library
library(xts)
library(dygraphs)

### Input
rm(list=ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
getwd()
data = read.csv("PCA_Preprocessed_IBI.csv")

### Change delta timing into time stamp
str(data)

# Convert character times to POSIXct
propBoutIEItime <- as.POSIXct(data$propBoutIEItime, format="%Y-%m-%d %H:%M:%OS")

# Create an xts object
data_xts <- xts(1/data$propBoutIEI, order.by=propBoutIEItime)

# Plot IEI time using dygraphs
dygraph(data_xts, main="propBoutIEI over Time") %>%
  dyAxis("y", label = "propBoutIEI") %>%
  dyAxis("x", label = "Time")



### Subset the dataframe for plotting
subset_begin <- c(200000)
subset_end <- c(200500)
data2<- data[subset_begin:subset_end,]

### Plotting
# speed ~ time
don <- xts(x = data2$speed, order.by = data2$real_time)
dygraph(don, main = "Speed ~ Time", ylab = "Speed (mm/s)", xlab = "Time (s)") %>%
  dyOptions(labelsUTC = TRUE, fillGraph=TRUE, fillAlpha=0.1, drawGrid = FALSE, colors="#D8AE5A") %>%
  dyRangeSelector() %>%
  dyCrosshair(direction = "vertical") %>%
  dyHighlight(highlightCircleSize = 5, highlightSeriesBackgroundAlpha = 0.2, hideOnMouseOut = FALSE)  %>%
  dyRoller(rollPeriod = 1)
  dy


# pitch ~ time
don2 <- xts(x = data2$pitch, order.by = data2$real_time)
dygraph(don2, main = "Pitch ~ Time", ylab = "Pitch (degree)", xlab = "Time (s)") %>%
  dyOptions(labelsUTC = TRUE, fillGraph=TRUE, fillAlpha=0.1, drawGrid = FALSE, colors="#D8AE5A") %>%
  dyRangeSelector() %>%
  dyCrosshair(direction = "vertical") %>%
  dyHighlight(highlightCircleSize = 5, highlightSeriesBackgroundAlpha = 0.2, hideOnMouseOut = FALSE)  %>%
  dyRoller(rollPeriod = 1) 


