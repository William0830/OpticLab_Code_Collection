import time
from matplotlib import pyplot as plt
import numpy as np

def step_update(i, j, ints):
    ints[i, j] = np.random.normal(loc=2000, scale=1000, size=1)
    return ints

def live_update_demo(len):
    print(len)
    xlim = (0, 100)
    ylim = (0, 100)

    xnodes = np.linspace(xlim[0], xlim[1],len)
    ynodes = np.linspace(ylim[0], ylim[1],len)

    X, Y = np.meshgrid(xnodes, ynodes, indexing='ij')
    ints = np.zeros_like(X)
    answers = np.random.normal(loc=2000, scale=1000, size=(len, len))


    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    img = ax1.imshow(ints, origin = 'lower', extent = (*xlim, *ylim), vmin=100, vmax=10000, interpolation="None", cmap="Spectral_r")
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    ax1.set_xlabel('x (µm)')
    ax1.set_ylabel('y (µm)')

    # text = ax1.text(0.8,0.5, "")
    fig.canvas.draw()   # note that the first draw comes before setting data 
        # cache the background
    axbackground = fig.canvas.copy_from_bbox(ax1.bbox)

    plt.show(block=False)


    # t_start = time.time()
    # k=0.
    times = []
    for i in range(xnodes.shape[0]):
        for j in range(ynodes.shape[0]):
            timea = time.time()
            # ints = step_update(i, j, ints)
            ints[i, j] = answers[i, j]
            img.set_data(ints)
            # tx = 'Mean Frame Rate:\n {fps:.3f}FPS'.format(fps= ((k+1) / (time.time() - t_start)) ) 
            # text.set_text(tx)
            # #print tx
            # k+=1
            fig.canvas.restore_region(axbackground)
            ax1.draw_artist(img)
            # ax1.draw_artist(text)
            fig.canvas.blit(ax1.bbox)
            fig.canvas.flush_events()
            timeb = time.time()
            times.append(timeb - timea)

    # with(open('times.txt', 'w')) as f:
    #     f.write(str(times))
    return np.mean(times)

times = [live_update_demo(int(i)) for i in np.linspace(5,200, 15)]  # 175 fps
#live_update_demo(False) # 28 fps
fig2 = plt.figure()
plt.plot(np.linspace(5,200, 15), times)   
# plt.hist(np.log10(times), bins=100)
plt.show(block=True)
