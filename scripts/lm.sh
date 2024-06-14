PYTHONPATH=. python src/lm.py --lm bert --mask-mode=prob --tokenize-prob 0.25 --epochs 100 --validate-every 10 --wandb-name bert_mask_prob --wandb-group lm --wandb-mode disabled
PYTHONPATH=. python src/lm.py --lm bert --mask-mode=end --epochs 100 --validate-every 10 --wandb-name bert_mask_end --wandb-group lm --wandb-mode disabled