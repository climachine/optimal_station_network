import numpy as np
from scipy.spatial.distance import pdist, squareform
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import regionmask

# station data
largefilepath = '/net/so4/landclim/bverena/large_files/'
df = xr.open_dataset(f'{largefilepath}df_gaps.nc').load()
df = df['mrso']

# select the stations still active
inactive_networks = ['HOBE','PBO_H20','IMA_CAN1','SWEX_POLAND','CAMPANIA',
                     'HiWATER_EHWSN', 'METEROBS', 'UDC_SMOS', 'KHOREZM',
                     'ICN','AACES','HSC_CEOLMACHEON','MONGOLIA','RUSWET-AGRO',
                     'CHINA','IOWA','RUSWET-VALDAI','RUSWET-GRASS']
df = df.where(~df.network.isin(inactive_networks), drop=True)

# remove all stations with less than 10 years of meas
count = (~np.isnan(df)).resample(time="1m").sum()
df = df.resample(time='1m').mean()
df = df.where(count >= 16)
df = df.where(np.isnan(df).sum(dim="time") >= 10 * 12)

# normalise
datamean = df.mean(dim='time')
datastd = df.std(dim='time')
df = (df - datamean) / datastd

# calculate anomalies
clim = df.groupby('time.month').mean()
df = df.groupby("time.month") - clim

# sort by country
df = df.sortby('country')

# distance matrix # TODO in km, not latlon
dist = squareform(pdist(np.array(list([df.lat.values, df.lon.values])).T))
np.fill_diagonal(dist, np.nan) # inplace

# corr matrix
corrmatrix = df.to_pandas().corr(method='spearman',min_periods=24).values
np.fill_diagonal(corrmatrix, np.nan) # inplace

# similarity cutoff
dist[np.isnan(corrmatrix)] = np.nan
#dist[corrmatrix < 0.7] = np.nan
allcorr = corrmatrix.copy()
corrmatrix[corrmatrix < 0.7] = np.nan

proj = ccrs.Robinson()
transf = ccrs.PlateCarree()

hull = []
for s in range(df.shape[1]):
    corr = corrmatrix[s, :]
    d = dist[s, :]
    no_stations = d[~np.isnan(corr)].size
    allc = allcorr[s,:]
    print(no_stations)

    idxs = np.where(~np.isnan(corr))[0]
    idxs2 = np.where(~np.isnan(allc))[0]
    #fig = plt.figure(figsize=(10,5))
    #ax = fig.add_subplot(111, projection=proj)
    #ax.set_title(f'number of similar stations: {no_stations}')
    ##ax.set_extent([-180, 180, -90, 90], crs=proj)
    #ax.coastlines()
    #ax.scatter(df.lon, df.lat, c='lightgrey', transform=transf)
    #ax.scatter(df.lon[idxs2], df.lat[idxs2], c='lightblue', transform=transf, edgecolors='black')
    #ax.scatter(df.lon[idxs], df.lat[idxs], c='lightgreen', transform=transf, edgecolors='black')
    #ax.scatter(df.lon[s], df.lat[s], c='red', transform=transf, edgecolors='black')
    #plt.show()
    ##import IPython; IPython.embed()
    ##plt.savefig(f'corrmaps_{s:04}.png')
    ##plt.close()

    #continue
    if no_stations == 0:
        hull.append(0)
    elif no_stations == 1:
        tmp = d[~np.isnan(corr)].item()
        hull.append(tmp)
    else:
        tmp1 = d[~np.isnan(corr)].max()
        hull.append(tmp1)
        # TODO: missing hull correction 90%
        #allc = allcorr[s,:]
        #tmp2 = allc[(d < tmp1) & (~np.isnan(allc))]
        #print('neighbors:', tmp2.size)
        #import IPython; IPython.embed()

        ## plot
        #fig = plt.figure(figsize=(10,5))
        #ax = fig.add_subplot(111)


fig = plt.figure(figsize=(10,5))
ax = fig.add_subplot(111, projection=proj)
ax.coastlines()
im = ax.scatter(df.lon, df.lat, c=hull, transform=transf)
cbar_ax = fig.add_axes([0.9, 0.2, 0.02, 0.5]) # left bottom width height
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label('distance in lat/lon space')
plt.show()
