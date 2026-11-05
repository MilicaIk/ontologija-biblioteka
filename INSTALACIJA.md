# Како се репозиторијум поставља на GitHub

Из фасцикле у коју сте распаковали архиву:

    git init
    git add .
    git commit -m "Онтологија библиотека у Википодацима, верзија уз рад"
    git branch -M main

Направите празан репозиторијум на GitHub-у (без README-а), па:

    git remote add origin https://github.com/KORISNIK/ontologija-biblioteka.git
    git push -u origin main

Ознака за верзију која је објављена у раду:

    git tag -a v1.0 -m "Верзија објављена у Читалишту 2026"
    git push origin v1.0

## DOI преко Zenodo

1. Пријава на https://zenodo.org преко GitHub налога.
2. У Zenodo → GitHub укључити прекидач поред овог репозиторијума.
3. На GitHub-у направити издање (Releases → Draft a new release) од ознаке v1.0.
4. Zenodo сам преузима издање и додељује му DOI.

Добијају се два DOI-ја: један за ово издање и један заједнички, који увек
води на најновије. У раду се наводи DOI издања v1.0, да читалац види тачно
оно што је приказано на слици.
