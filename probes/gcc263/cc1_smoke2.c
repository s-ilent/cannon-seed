/* cc1 modified-compiler smoke, shape 2 (store consumer).
 *
 * The color-war experiment's mechanism smoke, window cron-20261022-0158
 * (recreation of the cron-20261022-0043 store-consumer variant; the
 * repo-external copies were eaten by the rollback, so the units now
 * live in-repo).
 *
 *   t = a; *gp = t - t; y0 = y0 + t;
 *
 * The store is never sweep-dead (delete_dead_from_cse keeps it), so this
 * is the shape the milestone-3 guard is aimed at: with the fold_rtx entry
 * short-circuit (GUARD 3, tools/patch_cc1_263.sh) the subtract's reads
 * should survive cse2 - the success signature is the patched .flow
 * showing the 'a' register count +1 (or more) over the stock .flow with
 * the FINAL RENDERS identical (combine folds the pair via LOG_LINKS and
 * deletes it, exactly the stock pipeline's output).
 *
 * KNOWN RESULT (cron-20261022-0043): without GUARD 3 the subtract died
 * to the associate path (simplify_plus_minus's negs[] pair-merge routed
 * back into a fold door the M2 guards did not close).
 */

extern long a;
extern long y0;
extern long *gp;

void cc1_smoke2 (void)
{
    long t = a;
    *gp = t - t;
    y0 = y0 + t;
}
