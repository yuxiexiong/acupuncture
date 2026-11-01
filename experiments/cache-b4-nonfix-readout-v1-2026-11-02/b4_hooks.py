"""B4 readout hook on the G-layer gated RMSNorm output (`linear_attn.norm`, input of out_proj).  At a single-token score
step its output is [NV, HD]: row h = value head h.  Modes: None (record only), 'clamp' (non-FIX rows <- donor rows),
'add' (non-FIX rows <- BF16(row + delta)).  FIX rows are never written by the hook."""
NV, HD = 32, 128


class ReadoutHook:
    def __init__(self, layers, nonfix):
        """layers: {l: (norm_module, out_proj_weight)}; nonfix: {l: bool tensor [NV]} (True = not a FIX head)."""
        self.layers, self.nonfix = layers, nonfix
        self.key, self.mode, self.specs = None, None, {}
        self.rec, self.hits, self.handles = {}, {}, []

    def arm(self, key, mode=None, specs=None):
        self.key, self.mode, self.specs = key, mode, (specs or {})

    def disarm(self):
        self.key, self.mode, self.specs = None, None, {}

    def _hook(self, l):
        def fn(_m, _a, out):
            import torch
            import torch.nn.functional as Fn
            if self.key is None:
                return None
            assert tuple(out.shape) == (NV, HD), ('unexpected norm output shape', tuple(out.shape))
            h = self.hits.setdefault(self.key, {})
            h[l] = h.get(l, 0) + 1
            pre = out.detach().clone()
            W = self.layers[l][1]
            row = {'pre': pre, 'outproj_pre': Fn.linear(pre.reshape(1, 1, -1), W)[0, 0].detach().clone()}
            new = None
            if self.mode is not None and l in self.specs:
                m = self.nonfix[l].to(out.device)
                new = out.clone()
                if self.mode == 'clamp':
                    new[m] = self.specs[l].to(out.device, out.dtype)[m]
                elif self.mode == 'add':
                    new[m] = (out[m].float() + self.specs[l].to(out.device, torch.float32)[m]).to(out.dtype)
                else:
                    raise ValueError(self.mode)
                assert torch.equal(new[~m], out[~m]), ('FIX rows written', l)
                row['post'] = new.detach().clone()
            self.rec.setdefault(self.key, {})[l] = row
            return new
        return fn

    def __enter__(self):
        for l, (norm, _w) in self.layers.items():
            self.handles.append(norm.register_forward_hook(self._hook(l)))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        self.disarm()
        return False
