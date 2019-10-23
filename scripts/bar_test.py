from progress.bar import Bar
from tqdm import tqdm

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        if self.count > 0:
          self.avg = self.sum / self.count


def bar_test():
  num_iters = 4000
  bar = Bar('{}/{}'.format('opt.task', 'opt.exp_id'), max=num_iters)
  bar.width=4
  data_time, batch_time = AverageMeter(), AverageMeter()



  pbar=tqdm(total=num_iters)

  for i in range(num_iters):
    phase = 'trains'
    iter_id = i
    epoch = 0
    # bar.suffix = '{phase}: [{0}][{1}/{2}]|Tot: {total:} |ETA: {eta:} '.format(
    #   epoch, iter_id, num_iters, phase=phase,
    #   total=bar.elapsed_td, eta=bar.eta_td)

    bar.suffix = '{phase}: [{0}]'.format(
      epoch,phase=phase)

    bar.suffix = bar.suffix + '|{} {:.4f} '.format('loss', 2.3014)
    bar.suffix = bar.suffix + '|{} {:.4f} '.format('hm_loss', 2.3014)
    bar.suffix = bar.suffix + '|{} {:.4f} '.format('wh_loss', 2.3014)
    bar.suffix = bar.suffix + '|{} {:.4f} '.format('off_loss', 2.3014)

    data_time.update(10)
    batch_time.update(20)

    bar.suffix = bar.suffix + '|Data {dt.val:.3f}s({dt.avg:.3f}s) |Net {bt.avg:.3f}s'.format(dt=data_time,
                                                                                             bt=batch_time)
    # print("\r")

    # bar.next()

    pbar.set_description(bar.suffix)
    pbar.update(1)

    # print('{}/{}| {}'.format('opt.task', 'opt.exp_id', bar.suffix))

    

  bar.finish()

if __name__ == '__main__':
    bar_test()  