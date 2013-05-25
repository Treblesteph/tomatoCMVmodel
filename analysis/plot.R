# load data
library(ggplot2)
library(reshape)
sv <- read.csv('../season_visits.csv')
thousandseasons <- read.csv('../1000_seasons.csv')
hundredseasons <- thousandseasons[thousandseasons$season <= 100,]
fortyseasons <- thousandseasons[thousandseasons$season <= 40,]

linePlot <- function(df, size) {
  # plot susceptible vs resistant for 1000 seasons
  pd <- position_dodge(0)  # in case error bars or points overlap, they can be dodged by setting to 0.1
  ggplot(data=df,
         aes(x=season, y=mean, colour=population)) +
    geom_errorbar(aes(ymin=mean-sem, ymax=mean+sem), width=.1, position=pd) +
    geom_line(position=pd) +
    # geom_point(position=pd, size=3, shape=21, fill="white") + # 21 is filled circle
    scale_colour_hue(name="Population", # Legend label, use darker colors
                     l=40) + # Use darker colors, lightness=40
    ylab("Population size") +
    xlab("Season") +
    ggtitle(paste("Size of resistant and susceptible populations over", size, "seasons")) +
    theme_bw() +
    theme(legend.justification=c(1,0), legend.position=c(0.95,0.5)) # Position legend in mid right
}

stackedBarPlot <- function(df, size) {
  # same but as porportional stacked bars
  ggplot(data=df,
         aes(x=season, y=mean, fill=population)) +
    geom_bar(position="fill", stat="identity", width=0.99) +
    ylab("Proportion of popoulation") +
    xlab("Season") +
    scale_fill_hue(name="Population", # Legend label, use darker colors
                     l=30) +
    ggtitle(paste("Proportion of resistant and susceptible populations over", size, "seasons")) +
    theme_bw() +
    theme(legend.justification=c(1,0), legend.position=c(0.95,0.5)) # Position legend in mid right
}

pdf("testplots.pdf")
linePlot(thousandseasons, "1000")
stackedBarPlot(thousandseasons, "1000")
linePlot(hundredseasons, "100")
stackedBarPlot(hundredseasons, "100")
linePlot(fortyseasons, "40")
stackedBarPlot(fortyseasons, "40")
dev.off()