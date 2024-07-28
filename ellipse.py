import numpy as np

def ellipse(center1, center2, nb):
    # Centres de l'ellipse
    center_x = center1[0]
    center_y = center1[1]
    center_x2 = center2[0]
    center_y2 = center2[1]
    # Distance entre les deux centres
    distance = np.sqrt((center_x2 - center_x) ** 2 + (center_y2 - center_y) ** 2)
    # Centre de l'ellipse est le milieu de nos deux points
    h, k = (center_x + center_x2) / 2, (center_y + center_y2) / 2
    # Longueur du grand axe et du petit axe
    a = distance # la moitié de la distance de chaque côté de nos points. 
    b = distance/2 # On peut s'éloigner perpendiculairement du vol d'oiseau à un maximum de la moitié de la distance entre les deux points
    # Rotation de l'ellipse pour s'orienter selon l'axe des points de départ et d'arrivée
    rot = np.arctan2(center_y2 - center_y, center_x2 - center_x)
    # Calcul des points de l'ellipse selon sa formulaire mathématique
    theta = np.linspace(0, 2*np.pi, nb)
    x = h + a * np.cos(theta) * np.cos(rot) - b * np.sin(theta) * np.sin(rot)
    y = k + a * np.cos(theta) * np.sin(rot) + b * np.sin(theta) * np.cos(rot)
    # On créé la liste des points au format pris par mongodb
    res = []
    for i in range(len(x)):
        res.append([x[i],y[i]])
    # 
    res.append([x[0],y[0]])
    return res
