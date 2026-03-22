import matplotlib as mpl
import os
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .plt_tools import set_font_type
import warnings
import networkx as nx



def plt_categorical_combined(
    data:pd.DataFrame, 
    x:str, 
    y:str, 
    units:str, 
    row:str=None, 
    col:str=None, 
    errorbar=None, 
    sharey=True, 
    sns_palette='colorblind', 
    markertype='_', 
    height=3, 
    aspect=0.8,
    related=False,
    size=6,
    alpha=0.5,
    overlay_func = sns.swarmplot,
    col_order=None,
    estimator=np.nanmean
    ):
    
    """build upon sns.catplot(), plots mean y_name vs x_name with individual repeats. Repeats are plotted as stripplot if number of repeats are different among groups defined by x_name, otherwise, repeats are connected.
    the errorbar arg requires Seaborn v0.12 to work.

    Args:
        data (pd.DataFrame): Dataframe with one value per "unit". Can be achieved using: data.groupby([x_name, gridcol, gridrow, units]).mean().reset_index()
        x_name (str): Column to plot on the X axis.
        y_name (str): Column to plot on the Y axis. 
        gridrow (str): Categorical variables that will determine the faceting of the grid.
        gridcol (str): Categorical variables that will determine the faceting of the grid.
        units (str): Units for plotting individual repeats. see sns.lineplot() units arg.
        errorbar (optional): Defines type of error bars to plot. see seaborn.catplot errorbar arg. Defaults to None.
        sharey (bool, optional): Whether to share Y axis ticks. Defaults to True.
        sns_palette (str, optional): Color palettes. Defaults to 'colorblind'.
        height (int, optional): Height of the graph in inches. Defaults to 4.
        aspect (float, optional): aspect ratio of the graph. Defaults to 0.8.
    """
    set_font_type()
    cat_cols = [x, units, row, col]
    cat_cols = [ele for ele in cat_cols if ele is not None]

    if_one_val_per_rep = data.groupby(cat_cols).size().max()
    if if_one_val_per_rep > 1:
        data = data.groupby(cat_cols)[y].mean().reset_index()
    else:
        data = data.sort_values(by=cat_cols).reset_index(drop=True)
            
    assert_repeats = len(set(data.groupby([x])[units].apply(lambda x: len(x.unique())).values))
    
    if not related:
        assert_repeats = 0

        
    g = sns.catplot(
        data = data,
        col = col,
        row = row,
        # hue = x,
        x = x,
        y = y,
        kind = 'point',
        sharey = sharey,
        palette = sns_palette,
        errorbar = errorbar,
        markers = [markertype]*len(set(data[x])),
        height = height,
        aspect = aspect,
        col_order=col_order,
        estimator=estimator
        )
    if assert_repeats == 1:
        g.map(sns.lineplot,x,y,
            estimator=None,
            units=units,
            data = data,
            sort=False,
            color='grey',
            alpha=alpha,
            zorder=0,
            )
    else:
        if overlay_func:
            g.map(overlay_func,x,y,
                data = data,
                color='grey',
                alpha=alpha,
                zorder=0,
                order=data[x].unique().sort(),
                s=size,
            )
    g.add_legend()
    sns.despine(offset=10, trim=False)
    return g


def plt_categorical_grid2(
    data:pd.DataFrame, 
    x_name:str, 
    y_name:str, 
    units:str, 
    gridrow:str=None, 
    gridcol:str=None, 
    errorbar=None, 
    sharey=True, 
    sns_palette='colorblind', 
    markertype='d', 
    height=3, 
    aspect=0.8,
    method='mean'
    ):
    
    """build upon sns.catplot(), plots mean y_name vs x_name with individual repeats. Repeats are plotted as stripplot if number of repeats are different among groups defined by x_name, otherwise, repeats are connected.
    the errorbar arg requires Seaborn v0.12 to work.

    Args:
        data (pd.DataFrame): Dataframe with one value per "unit". Can be achieved using: data.groupby([x_name, gridcol, gridrow, units]).mean().reset_index()
        x_name (str): Column to plot on the X axis.
        y_name (str): Column to plot on the Y axis. 
        gridrow (str): Categorical variables that will determine the faceting of the grid.
        gridcol (str): Categorical variables that will determine the faceting of the grid.
        units (str): Units for plotting individual repeats. see sns.lineplot() units arg.
        errorbar (optional): Defines type of error bars to plot. see seaborn.catplot errorbar arg. Defaults to None.
        sharey (bool, optional): Whether to share Y axis ticks. Defaults to True.
        sns_palette (str, optional): Color palettes. Defaults to 'colorblind'.
        height (int, optional): Height of the graph in inches. Defaults to 4.
        aspect (float, optional): aspect ratio of the graph. Defaults to 0.8.
    """
    set_font_type()
    cat_cols = [x_name, units, gridrow, gridcol]
    cat_cols = [ele for ele in cat_cols if ele is not None]

    if_one_val_per_rep = data.groupby(cat_cols).size().max()
    if if_one_val_per_rep > 1:
        if method == 'mean':
            data = data.groupby(cat_cols)[y_name].mean().reset_index()
        if method == 'median':
            data = data.groupby(cat_cols)[y_name].median().reset_index()
    else:
        data = data.sort_values(by=cat_cols).reset_index(drop=True)
    
    assert_repeats = []    
    assert_df = pd.DataFrame(data.groupby([x_name])[units].apply(lambda x: x.unique()).reset_index()[units].tolist())  
    for col in assert_df:
        assert_repeats.append(len(assert_df[col].unique()))
        
    g = sns.catplot(
        data = data,
        col = gridcol,
        row = gridrow,
        hue = x_name,
        x = x_name,
        y = y_name,
        kind = 'point',
        sharey = sharey,
        palette = sns_palette,
        errorbar = errorbar,
        markers = [markertype]*len(set(data[x_name])),
        height = height,
        aspect = aspect,

        )
    if np.max(assert_repeats) == 1:
        g.map(sns.lineplot,x_name,y_name,
            estimator=None,
            units=units,
            data = data,
            sort=False,
            color='grey',
            alpha=0.2,
            zorder=0,
            )
    else:
        g.map(sns.stripplot,x_name,y_name,
            data = data,
            color='lightgrey',
            zorder=0,
            order=data[x_name].unique().sort(),
            )
    g.add_legend()
    sns.despine(offset=10, trim=False)
    return g

def plt_categorical_grid(
    data:pd.DataFrame, 
    x_name:str, 
    y_name:str, 
    gridrow:None, 
    gridcol:None, 
    units:str, 
    errorbar=None, 
    sharey=True, 
    sns_palette='colorblind', 
    markertype='d', 
    height=4, 
    aspect=0.8,
    ):
    
    """build upon sns.catplot(), plots mean y_name vs x_name with individual repeats. Repeats are plotted as stripplot if number of repeats are different among groups defined by x_name, otherwise, repeats are connected.
    the errorbar arg requires Seaborn v0.12 to work.

    Args:
        data (pd.DataFrame): Dataframe with one value per "unit". Can be achieved using: data.groupby([x_name, gridcol, gridrow, units]).mean().reset_index()
        x_name (str): Column to plot on the X axis.
        y_name (str): Column to plot on the Y axis. 
        gridrow (str): Categorical variables that will determine the faceting of the grid.
        gridcol (str): Categorical variables that will determine the faceting of the grid.
        units (str): Units for plotting individual repeats. see sns.lineplot() units arg.
        errorbar (optional): Defines type of error bars to plot. see seaborn.catplot errorbar arg. Defaults to None.
        sharey (bool, optional): Whether to share Y axis ticks. Defaults to True.
        sns_palette (str, optional): Color palettes. Defaults to 'colorblind'.
        height (int, optional): Height of the graph in inches. Defaults to 4.
        aspect (float, optional): aspect ratio of the graph. Defaults to 0.8.
    """
    set_font_type()
    data.sort_values(by=x_name,inplace=True)
    
    assert_repeats = data.groupby([x_name,units]).size().min()
    
    g = sns.catplot(
        data = data,
        col = gridcol,
        row = gridrow,
        hue = x_name,
        x = x_name,
        y = y_name,
        kind = 'point',
        sharey = sharey,
        palette = sns_palette,
        errorbar = errorbar,
        markers = [markertype]*len(set(data[x_name])),
        height = height,
        aspect = aspect,
        )
    if assert_repeats > 1:
        g.map(sns.lineplot,x_name,y_name,
            estimator=None,
            units=units,
            data = data,
            sort=False,
            color='grey',
            alpha=0.2,
            zorder=0,
            )
    else:
        g.map(sns.stripplot,x_name,y_name,
            data = data,
            color='lightgrey',
            zorder=0,
            order=data[x_name].unique().sort(),
            )
    g.add_legend()
    sns.despine(offset=10, trim=False)
    return g

def plt_network_graphs(total_features, fig_dir, sort_by_feature=[], cond_sep=None, extracted_features:pd.DataFrame=pd.DataFrame()):
# #     % norm by outbound
    if extracted_features.empty:
        extracted_features = total_features
        
    G_master = nx.from_pandas_edgelist(total_features.groupby(['cluster','to_cluster']).size().reset_index(), 'cluster', 'to_cluster', create_using=nx.DiGraph()) 
    pos = nx.circular_layout(G_master)
    nCluster = len(list(G_master))

    if sort_by_feature:
        if type(sort_by_feature) == str:
            sort_by_feature = [sort_by_feature]
            
    for sel_feature_to_sort in sort_by_feature:
        # % colored by outbound and reorder
        sorted_cluster = total_features.groupby('cluster').mean().sort_values(by=sel_feature_to_sort).reset_index().reset_index()
        cluster_seq = sorted_cluster['cluster']

        connected_bouts = extracted_features.loc[:,['cluster','to_cluster','expNum','cond0','cond1',sel_feature_to_sort]]

        graph_df = connected_bouts.groupby(['cluster','to_cluster']).size().reset_index()
        graph_df.columns = ['from_cluster','to_cluster','weight']

        # normalize by the number of bouts per cluster
        graph_df = graph_df.merge(connected_bouts.groupby('cluster').size().to_frame(name='total_bouts').reset_index(),left_on='from_cluster', right_on='cluster')
        graph_df = graph_df.merge(sorted_cluster[['cluster',sel_feature_to_sort]], left_on='from_cluster', right_on='cluster')
        graph_df = graph_df.assign(
            weight_norm = graph_df['weight']/graph_df['total_bouts']
        )

        # pos = nx.circular_layout(G)

        pos_alt = {}
        for i, key in enumerate(cluster_seq):
            pos_alt[key] = pos[i]

        H = nx.from_pandas_edgelist(graph_df, 'from_cluster', 'to_cluster', ['weight_norm',sel_feature_to_sort], create_using=nx.DiGraph()) 
        G = nx.DiGraph()
        G.add_nodes_from(sorted(H.nodes(data=True)))
        G.add_edges_from(H.edges(data=True))
        # pos = nx.circular_layout(G)
        # labels = nx.get_edge_attributes(G,'weight_norm')

        edges = G.edges()
        weights = np.array([G[u][v]['weight_norm'] for u,v in edges])
        c_feature = np.array([G[u][v][sel_feature_to_sort] for u,v in edges])

        weights_adj = weights/weights.max()*4
        alpha = np.log((1+weights/np.max(weights))*(np.e/2))
        # c = sns.color_palette()
        c = sns.diverging_palette(250, 30, l=65, center="dark", as_cmap=True)
        c_list = sns.diverging_palette(250, 30, l=65, center="dark", n=nCluster)
        
        fig, (ax1) = plt.subplots(1, figsize=(8,5))
        nx.draw_networkx_edges(G,pos=pos_alt,
                            alpha = (alpha-alpha.min())/(1-alpha.min()),
                            width = weights_adj,
                            connectionstyle='arc3, rad=0.1',
                            edge_color = c_feature,
                            edge_cmap = c,
                            ax=ax1,
                            #    arrowstyle='-|>' 
                            )

            
        nx.draw_networkx_nodes(
            G,
            pos=pos_alt,
            ax=ax1,
            node_color=[c_list[i] for i in cluster_seq.sort_values().index]
        )
        nx.draw_networkx_labels(
            G,
            pos=pos_alt,
            font_color='w',
            ax=ax1
        )

        edges2 = nx.draw_networkx_edges(G,pos=pos_alt,
                            alpha = 1,
                            connectionstyle='arc3, rad=0.1',
                            edge_color = c_feature,
                            width=0,
                            edge_cmap = c,
                            ax=ax1,
                            arrows=False
        )
        cbar = plt.colorbar(edges2, ax=ax1)
        cbar.ax.set_ylabel(sel_feature_to_sort, rotation=270)

        plt.savefig(f"{fig_dir}/graph_c{nCluster}_outbound_by{sel_feature_to_sort}_{cond_sep}.pdf",format='PDF')
        
        ############# by total

        H = nx.from_pandas_edgelist(graph_df, 'from_cluster', 'to_cluster', ['weight',sel_feature_to_sort], create_using=nx.DiGraph()) 
        G = nx.DiGraph()
        G.add_nodes_from(sorted(H.nodes(data=True)))
        G.add_edges_from(H.edges(data=True))
        
        labels = nx.get_edge_attributes(G,'weight')

        edges = G.edges()
        weights = np.array([G[u][v]['weight'] for u,v in edges])
        c_feature = np.array([G[u][v][sel_feature_to_sort] for u,v in edges])

        weights_adj = weights/weights.max()*4
        alpha = np.log((1+weights/np.max(weights))*(np.e/2))
        # c = sns.color_palette("flare", as_cmap=True)
        # c = sns.light_palette("black", as_cmap=True)
        c = sns.diverging_palette(250, 30, l=65, center="dark", as_cmap=True)
        c_list = sns.diverging_palette(250, 30, l=65, center="dark", n=nCluster)

        fig, (ax1) = plt.subplots(1, figsize=(8,5))
        nx.draw_networkx_edges(G,pos=pos_alt,
                            alpha = alpha,
                            width = weights_adj,
                            connectionstyle='arc3, rad=0.1',
                            edge_color = c_feature,
                            edge_cmap = c,
                            #    arrowstyle='-|>' 
                            )

            
        nx.draw_networkx_nodes(
            G,
            pos=pos_alt,
            ax=ax1,
            node_color=[c_list[i] for i in cluster_seq.sort_values().index]
        )
        nx.draw_networkx_labels(
            G,
            pos=pos_alt,
            font_color='w',
            ax=ax1
        )
        edges2 = nx.draw_networkx_edges(G,pos=pos_alt,
                    alpha = 1,
                    connectionstyle='arc3, rad=0.1',
                    edge_color = c_feature,
                    width=0,
                    edge_cmap = c,
                    ax=ax1,
                    arrows=False
        )
        cbar = plt.colorbar(edges2, ax=ax1)
        cbar.ax.set_ylabel(sel_feature_to_sort, rotation=270)

        plt.savefig(f"{fig_dir}/graph_c{nCluster}_total_by{sel_feature_to_sort}_{cond_sep}.pdf",format='PDF')

    # pos = nx.circular_layout(G)
#     # labels = nx.get_edge_attributes(G,'weight_norm')

#     edges = G.edges()
#     weights = np.array([G[u][v]['weight_norm'] for u,v in edges])

#     weights_adj = weights/weights.max()*3
#     alpha = np.log((1+weights/np.max(weights))*(np.e/2))
#     # c = sns.color_palette("flare", as_cmap=True)
#     c = sns.light_palette("black", as_cmap=True)


#     fig = plt.figure(figsize=(7,5))
#     arrows = nx.draw_networkx_edges(G,pos=pos,
#                         alpha = alpha,
#                         width = weights_adj,
#                         connectionstyle='arc3, rad=0.1',
#                         edge_color = weights,
#                         edge_cmap = c,
#                         #    arrowstyle='-|>' 
#                         )

        
#     nx.draw_networkx_nodes(
#         G,
#         pos=pos,
#     )
#     nx.draw_networkx_labels(
#         G,
#         pos=pos,
#     )
#     plt.savefig(f"{fig_dir}/graph_c{nCluster}_normToCluster_{cond_sep}.pdf",format='PDF')

#     ############################
#     # % total

#     G = nx.from_pandas_edgelist(graph_df, 'from_cluster', 'to_cluster', 'weight', create_using=nx.DiGraph()) 
#     # pos = nx.circular_layout(G)
#     labels = nx.get_edge_attributes(G,'weight')

#     edges = G.edges()
#     weights = np.array([G[u][v]['weight'] for u,v in edges])

#     weights_adj = weights/weights.max()*3
#     alpha = np.log((1+weights/np.max(weights))*(np.e/2))
#     # c = sns.color_palette("flare", as_cmap=True)
#     c = sns.light_palette("black", as_cmap=True)


#     fig = plt.figure(figsize=(7,5))
#     arrows = nx.draw_networkx_edges(G,pos=pos,
#                         alpha = 1,
#                         width = weights_adj,
#                         connectionstyle='arc3, rad=0.1',
#                         edge_color = weights,
#                         edge_cmap = c,
#                         #    arrowstyle='-|>' 
#                         )

        
#     nx.draw_networkx_nodes(
#         G,
#         pos=pos,
#     )
#     nx.draw_networkx_labels(
#         G,
#         pos=pos,
#     )

#     plt.savefig(f"{fig_dir}/graph_c{nCluster}_totalBouts_{cond_sep}.pdf",format='PDF')
    
    ############################