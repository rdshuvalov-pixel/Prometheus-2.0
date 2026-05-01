# Первый push в GitHub

1. На github.com создайте **пустой** приватный репозиторий `prometheus-2` (без README).
2. В корне проекта:

```bash
cd "/path/to/Прометей 2.0"
git remote add origin https://github.com/<USER>/prometheus-2.git
git branch -M main
git push -u origin main
```

3. Проверка CI: вкладка Actions в репозитории после push ([.github/workflows/ci.yml](../.github/workflows/ci.yml)).
