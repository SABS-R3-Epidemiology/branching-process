##### BranchPro: inference of $R\_t$

In order to make predictions about how case numbers will evolve in the future, we require an estimate of the reproduction number $R\_t$. One common method of estimating $R\_t$ is to infer it (using Bayesian inference) from recent incidence data. Below, we do just that: given the incidence data for 30 days, we can infer the value of $R\_t$ over that time period. In a sense, this is the opposite (a.k.a. the inverse) of the *forward model*, where we used a known/assumed value for the reproduction number to predict future case numbers; now, we are using past case numbers to estimate the reproduction number. This is called an *inverse probem*.

The model also calculates a 95% *credible interval* for the reproduction number; this simply tells us that we are 95% sure that the value for $R$ (the reproduction number value assumed to be constant over the last $\tau$ days) lies between a lower and an upper bound. So, for example, for day 16, our model might calculate that $R\_{16}$ was most likely equal to 1.3 and that we are 95% sure that it lay between 1.0 and 1.5. This credible interval is an important output of the model because it highlights that we can only *estimate* values for $R\_t$ and also *quantifies the uncertainty* of the model.

 All of the code can be found on [our GitHub page](https://github.com/SABS-R3-Epidemiology/branchpro).
