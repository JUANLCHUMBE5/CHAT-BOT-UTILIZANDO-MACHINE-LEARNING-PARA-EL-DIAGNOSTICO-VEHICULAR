import pandas as pd

df = pd.read_csv('machine_learning/data/fase10/fase10_c1_metrics_by_class.csv')
top10 = df.sort_values(by='delta_f1', ascending=False).head(10)
for i, r in enumerate(top10.itertuples(), 1):
    print(f"{i}. **{r.clase}** (n={r.support}): F8.3 F1 = {r.f1_f83*100:.2f}% (P={r.precision_f83*100:.2f}%, R={r.recall_f83*100:.2f}%) -> C1 F1 = {r.f1_c1*100:.2f}% (P={r.precision_c1*100:.2f}%, R={r.recall_c1*100:.2f}%) | Delta F1 = {r.delta_f1*100:+.2f}% | Delta R = {r.delta_recall*100:+.2f}%")
