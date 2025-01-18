import networkx as nx
import numpy as np
import copy
import logging
import time


class LagrangeModel:
    def __init__(
            self, trips, blocks, backups, arc_dist, orig_kwh, bu_kwh,
            x_init, z_init, ub=None):
        self.src = (0, 0)
        self.sink = (0, 1)
        self.trips = trips
        self.nodes = self.trips + [self.src] + [self.sink]
        self.blocks = blocks
        self.n_blocks = len(blocks)
        self.backups = backups
        self.n_backups = len(backups)
        # arc_dist uses same coords for src and sink, which causes
        #   errors in networkx. Change it here.
        self.arc_dist = copy.copy(arc_dist)
        for (u, i, v, j) in arc_dist:
            if (v, j) == self.src:
                self.arc_dist[(u, i, *self.sink)] = self.arc_dist[u, i, v, j]
                self.arc_dist.pop((u, i, v, j))
        self.a_set = list(self.arc_dist.keys())
        self.orig_kwh = orig_kwh
        self.bu_kwh = bu_kwh
        if ub:
            self.ub = ub
        else:
            self.ub = np.infty

        # Build up some useful sets
        self.x_arcs_u = dict()
        for u in self.blocks:
            u_nodes = [self.src] + [self.sink] + [
                k for k in self.trips if k[0] == u]
            u_arcs = [(u, i, v, j) for (u, i, v, j) in self.a_set
                      if (u, i) in u_nodes and (v, j) in u_nodes]
            self.x_arcs_u[u] = u_arcs

        self.all_x_arcs = [k for u in self.blocks for k in self.x_arcs_u[u]]

        if x_init:
            self.x_init = x_init
        else:
            self.x_init = {k: 0 for u in self.blocks for k in self.x_arcs_u[u]}

        if z_init:
            self.z_init = copy.copy(z_init)
            for (b, u, i, v, j) in z_init:
                if (v, j) == self.src:
                    self.z_init[(b, u, i, *self.sink)] = self.z_init[
                        b, u, i, v, j]
                    self.z_init.pop((b, u, i, v, j))

        else:
            self.z_init = {(b, u, i, v, j): 0 for (u, i, v, j)
                           in self.a_set for b in self.backups}

    def get_shortest_path_z(self, costs, b):
        ebunch = [((u, i), (v, j), {'weight': costs[b, u, i, v, j]})
                  for (u, i, v, j) in self.a_set]
        g = nx.DiGraph()
        g.add_edges_from(ebunch)
        path = nx.bellman_ford_path(g, self.src, self.sink)
        opt_arcs = [(*path[i], *path[i + 1]) for i in range(len(path) - 1)]
        return opt_arcs

    def get_shortest_path_u(self, costs, u):
        u_nodes = [self.src] + [self.sink] + [
            k for k in self.trips if k[0] == u]
        ebunch = [((u, i), (v, j), {'weight': costs[u, i, v, j]})
                  for (u, i, v, j) in costs
                  if (u, i) in u_nodes and (v, j) in u_nodes]
        g = nx.DiGraph()
        g.add_edges_from(ebunch)
        path = nx.bellman_ford_path(g, self.src, self.sink)
        opt_arcs = [(*path[i], *path[i + 1]) for i in range(len(path) - 1)]
        return opt_arcs

    def update_mu(self, mu_k, x_k, z_k, theta_k):
        mu_out = dict()
        for (u, i) in mu_k:
            if (u, i) == self.src:
                sum_trips = self.n_blocks + self.n_backups
            elif (u, i) == self.sink:
                sum_trips = 0
            else:
                sum_trips = 1

            sum_x = sum(x_k[a] for a in self.a_set if a[:3] == (u, i, u))
            sum_z = sum(z_k[(b, *a)] for b in self.backups
                        for a in self.a_set if a[:2] == (u, i))
            mu_out[u, i] = mu_k[u, i] + theta_k * (sum_x + sum_z - sum_trips)
        return mu_out

    def update_lambda_b(self, lambda_k, z_k, theta_k):
        new_lambda_b = dict()
        for b in self.backups:
            new_lambda_b[b] = \
                np.maximum(0, lambda_k[b] + theta_k * (
                        sum(self.arc_dist[a] * z_k[(b, *a)] for a in self.a_set)
                        - self.bu_kwh[b]))
        return new_lambda_b

    def update_lambda_u(self, lambda_k, x_k, theta_k):
        new_lambda_u = dict()
        for u in self.blocks:
            new_lambda_u[u] = \
                np.maximum(
                    0, lambda_k[u] + theta_k * (
                        sum(self.arc_dist[a] * x_k[a] for a in self.x_arcs_u[u])
                        - self.orig_kwh[u]))
        return new_lambda_u

    def update_costs_z(self, lambda_b, mu):
        new_costs = dict()
        for b in self.backups:
            for (u, i, v, j) in self.a_set:
                depot_ct = 1 if (u, i) == self.src else 0
                new_costs[b, u, i, v, j] = depot_ct + mu[u, i] \
                    + self.arc_dist[u, i, v, j] * lambda_b[b]

        return new_costs

    def update_costs_x(self, lambda_u, mu):
        new_costs = dict()
        for u in self.blocks:
            for (v, i, w, j) in self.x_arcs_u[u]:
                new_costs[v, i, w, j] = mu[v, i] \
                        + self.arc_dist[v, i, w, j]*lambda_u[u]
        return new_costs

    def run_subgradient(self, max_itr=1000):
        start_time = time.time()

        # Initialize
        lambda_b = {b: 0 for b in self.backups}
        lambda_u = {u: 0 for u in self.blocks}
        mu = {(u, i): 0 for (u, i) in self.nodes}
        z_vals = self.z_init
        x_vals = self.x_init

        # TODO: try Newton's method step size if convergence is slow
        mthd = 'basic'
        best_obj = -np.infty
        best_obj_int = -np.infty
        for itr in range(1, max_itr):
            if mthd == 'basic':
                theta = 0.0001 / itr
            elif mthd == 'newton':
                # diff_b = [
                #     sum(self.arc_dist[a] * z_k[(b, *a)] for a in self.a_set)
                #     - self.bu_kwh[b])) for b in self.backups]
                # diff_u = [
                #     sum(self.arc_dist[a])
                # ]
                theta = None
            else:
                raise ValueError('Unrecognized method.')

            # Update lagrange multipliers
            lambda_b = self.update_lambda_b(lambda_b, z_vals, theta)
            lambda_u = self.update_lambda_u(lambda_u, x_vals, theta)
            mu = self.update_mu(mu, x_vals, z_vals, theta)

            # Solve subproblem for backup buses
            costs_b = self.update_costs_z(lambda_b, mu)
            opt_arcs_b = {
                b: self.get_shortest_path_z(costs_b, b) for b in self.backups}
            z_vals = {(b, u, i, v, j): 1 if (u, i, v, j) in opt_arcs_b[b]
                      else 0 for (u, i, v, j) in self.a_set
                      for b in self.backups}

            # Solve subproblem for original blocks
            costs_u = self.update_costs_x(lambda_u, mu)
            opt_arcs_u = {u: self.get_shortest_path_u(costs_u, u)
                          for u in self.blocks}
            x_vals = {k: 1 if k in opt_arcs_u[u] else 0
                      for u in self.blocks for k in self.x_arcs_u[u]}

            # Calculate objective value
            x_obj = sum(
                (mu[v, i] + lambda_u[u] * self.arc_dist[v, i, w, j]) * x_vals[
                    v, i, w, j] for u in self.blocks
                for (v, i, w, j) in self.x_arcs_u[u])
            depot_ct = {(u, i): 1 if (u, i) == self.src else 0
                        for (u, i) in self.nodes}
            z_obj = sum(
                (depot_ct[u, i] + mu[u, i] + lambda_b[b] * self.arc_dist[
                    u, i, v, j]) * z_vals[b, u, i, v, j]
                for (b, u, i, v, j) in z_vals)
            const = sum(mu[k] for k in mu) + sum(
                lambda_u[u] * self.orig_kwh[u] for u in self.blocks) + sum(
                lambda_b[b] * self.bu_kwh[b] for b in self.backups)
            obj_full = x_obj + z_obj - const

            if obj_full > best_obj:
                best_obj = obj_full
                best_obj_int = int(np.ceil(obj_full))
                logging.info(
                    'Iteration {}: New best objective function value {:.4f}. '
                    'Best integer bound {}.'.format(
                        itr, best_obj, best_obj_int))

            if best_obj_int == self.ub:
                logging.info(
                    'Lagrangian relaxation bound is equal to provided upper '
                    'bound, proving optimality!')
                break

        logging.info('Subgradient optimization completed in {:.2f} '
                     'seconds.'.format(time.time()-start_time))
        return best_obj

