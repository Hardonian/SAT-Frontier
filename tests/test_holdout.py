import json
import tempfile
import unittest
from pathlib import Path

from sat_frontier.generate import generate
from sat_frontier.holdout_guard import (
    check_overlap,
    prior_instance_hashes,
    verify_train_freeze,
)
from sat_frontier.policy_holdout import (
    CONFIG,
    CONFIG_SHA256,
    PREREG,
    PREREG_SHA256,
    ROOT,
    sha,
)


class HoldoutTests(unittest.TestCase):
    def test_preregistration_and_config_hashes(self):
        self.assertEqual(sha(CONFIG.read_bytes()), CONFIG_SHA256)
        self.assertEqual(sha(PREREG.read_bytes()), PREREG_SHA256)

    def test_train_freeze_matches_winner(self):
        winner = verify_train_freeze(ROOT)
        self.assertEqual(winner['candidate'], 'component')
        self.assertFalse(winner['holdout_consumed'])
        cfg = json.loads(CONFIG.read_bytes())
        self.assertEqual(cfg['split'], 'holdout')
        self.assertIn(winner['candidate'], cfg['candidates'])
        self.assertEqual(cfg['candidates'][winner['candidate']], winner['weights'])

    def test_holdout_instances_have_no_prior_overlap(self):
        cfg = json.loads(CONFIG.read_bytes())
        prior = prior_instance_hashes(ROOT / 'evidence')
        instances = [
            generate(family, cfg['n'], cfg['ratio'], seed).dimacs().encode()
            for family in cfg['families']
            for seed in cfg['seeds']
        ]
        self.assertEqual(len(instances), 120)
        seen = check_overlap(instances, prior)
        self.assertEqual(len(seen), 120)


if __name__ == '__main__':
    unittest.main()
