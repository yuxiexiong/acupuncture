"""Synthetic algebra checks only; no model or experiment data."""
import unittest
import torch
from analyse import geometry, receiver_mean, half_bin


class Tests(unittest.TestCase):
    def test_scalar_rotation_and_sign(self):
        c=torch.tensor([1.,0.],dtype=torch.float64)
        u=torch.tensor([2.,3.],dtype=torch.float64)
        for h in (2*c,-c,torch.tensor([1.,2.],dtype=c.dtype)):
            g,r=geometry(c,h)
            self.assertAlmostEqual(float((h-c)@u),(g['k']-1)*float(c@u)+float(r@u))
            self.assertAlmostEqual(float(r@c),0.)
        self.assertEqual(geometry(c,2*c)[0]['residual_fraction'],0.)
        self.assertEqual(geometry(c,-c)[0]['k'],-1.)

    def test_receiver_weighting_and_sign_order(self):
        rows=[{'receiver':'a','x':1.},{'receiver':'a','x':3.},{'receiver':'b','x':9.}]
        self.assertEqual(receiver_mean(rows,'x'),5.5)
        terms=[-2.,3.]
        self.assertEqual(sum(max(t,0) for t in terms),3.)
        self.assertEqual(sum(min(t,0) for t in terms),-2.)

    def test_bfloat_final_round_bound(self):
        self.assertEqual(half_bin(16.),.0625)
        self.assertEqual(half_bin(-16.),.0625)
        self.assertEqual(half_bin(15.),.03125)

    def test_rms_pullback(self):
        h=torch.tensor([.5,-1.,2.],dtype=torch.float64,requires_grad=True)
        gamma=torch.tensor([1.2,.7,1.1],dtype=h.dtype)
        v=torch.tensor([-.3,1.,2.],dtype=h.dtype);eps=1e-6
        rms=(h.square().mean()+eps).sqrt();loss=(v*gamma*h/rms).sum()
        actual=torch.autograd.grad(loss,h)[0]
        expected=gamma*v/rms-h*(h*gamma*v).sum()/(h.numel()*rms**3)
        torch.testing.assert_close(actual,expected,rtol=1e-12,atol=1e-12)


if __name__=='__main__':
    torch.set_num_threads(1)
    unittest.main()
