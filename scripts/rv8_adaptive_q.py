"""RV-8: online linear Q regression as a privileged-label headroom probe."""
from ri5_rich_k_state import run_experiment


def verdict(results):
    r = results['dataops']
    gain = 100*(r['LEARNED-Q']['final_routing_mean']-r['CLOSED-FORM']['final_routing_mean'])
    return dict(headroom_pp=gain, flag_large_gain=gain > 5, adopt=False,
                criterion='report learned-minus-closed-form headroom; flag >5pp; no automatic adoption')


if __name__ == '__main__':
    run_experiment('rv8', 'rv8_adaptive_q.json', {'CLOSED-FORM': {}, 'LEARNED-Q': {'learned': True}}, ['dataops'], verdict, seeds=10,
                   notes=['Online squared-error regression with three global coefficients, initialized (1,1,1), learning rate .05 and bounds [.01,10]. One post-verification gradient step per decision.',
                          'Target is one-hot best dimension by counterfactual increase in verified-action probability; ties choose lowest dimension. Full counterfactual labels are privileged training data; no evaluation labels enter updates.',
                          'Q retains category K multiplication. The probe estimates achievable headroom for this specified linear learner, not a mathematical upper bound over every trained router.'])
