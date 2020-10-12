# Regions clustering based on early transmission features of Covid-19

Code used for our paper "**Forecasting Covid-19 Dynamics in Brazil: A DataDriven Approach**":
<https://www.mdpi.com/1660-4601/17/14/5115>

![world_map](Images/map_world.png)

### Install
* Clone this repo:
```
git clone https://github.com/jorisguerin/clustering_covid
```
* Move to the base directory
```
cd path/to/clustering_covid
```
* Create and prepare conda environment:
```
conda env create -f environment.yml
```
* Activate conda environment
```
conda activate clustering_covid
```

You should be good to go, you can now start jupyter and run the notebook.

### Data sources
##### Covid data
- World & USA: <https://github.com/CSSEGISandData/COVID-19/>
- Brazil: <https://covid.saude.gov.br/>
- Italy: https://github.com/pcm-dpc/COVID-19

##### Population data
- China: <https://en.wikipedia.org/wiki/List_of_Chinese_administrative_divisions_by_population>
- Brazil: <https://en.wikipedia.org/wiki/List_of_Brazilian_states_by_population>
- Australia: <https://en.wikipedia.org/wiki/States_and_territories_of_Australia>
- Canada: <https://en.wikipedia.org/wiki/Population_of_Canada_by_province_and_territory>

**Note:** *All data files present in this github directory were saved on May 1st 2020, feel free to download updated versions with more recent data for new studies.*

### Citing
If you find this work useful in your research, please consider citing

```
@article{pereira2020forecasting,
title={Forecasting Covid-19 dynamics in Brazil: a data driven approach},
author={Pereira, Igor G and Guerin, Joris M and Junior, Andouglas G Silva and Distante, Cosimo and Garcia, Gabriel S and Goncalves, Luiz MG},
journal={arXiv preprint arXiv:2005.09475},
year={2020}
}
```

### Credit
Many of the content present in this repository were inspired by the excellent work in the following github repository: <https://github.com/ploner/coronavirus-clustering>
