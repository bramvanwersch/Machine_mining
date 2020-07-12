
colors = c(rgb(184, 98, 92,200, maxColorValue = 255), rgb(235, 173, 16, 200, maxColorValue = 255),
           rgb(58, 90, 120, 200, maxColorValue = 255), rgb(189, 99, 20, 200, maxColorValue = 255),
           rgb(10, 10, 10, 200, maxColorValue = 255), rgb(152, 196, 237, 200, maxColorValue = 255))
#iron gold zinc copper coal
mean=c(50, 70, 20, 30, 10, 100)
sd=c(30, 3, 5, 5, 50, 2)
x <- seq(0, 100,length=100)
lower.x <- 0
upper.x <- 100
step <- (upper.x - lower.x) / 1000

hx <- dnorm(x,mean[1],sd[1])
plot(x, hx, type ='l', xlab="Ore depth", ylab="probability",
     main="Ore distributions", col = colors[1], ylim = c(0,0.2))

cord.x <- c(lower.x,seq(lower.x,upper.x,step),upper.x)
cord.y <- c(0,dnorm(seq(lower.x,upper.x,step),mean[1], sd[1]),0)
polygon(cord.x,cord.y,col=colors[1])

for( i in 2:length(mean)){
  hx <- dnorm(x,mean[i],sd[i])
  lines(x, hx, col = colors[i])
  cord.x <- c(lower.x,seq(lower.x,upper.x,step),upper.x)
  cord.y <- c(0,dnorm(seq(lower.x,upper.x,step),mean[i], sd[i]),0)
  polygon(cord.x,cord.y,col=colors[i]) 
}

  