/* cc1 modified-compiler smoke, shape 1 (register consumer).
 *
 * The color-war experiment's mechanism smoke, window cron-20261022-0158
 * (recreation of the cron-20261022-0043 smoke1; the repo-external copies
 * were eaten by the rollback, so the units now live in-repo).
 *
 *   t = a; x = t - t; y = y0 + t; return y;
 *
 * With the MODIFIED-CC1 guards (tools/patch_cc1_263.sh) the self-kill
 * pair is expected to survive cse2 (the .flow tally counts the extra
 * reads) and vanish in combine - the final render must stay IDENTICAL
 * to the stock render.  Run tools/cc1_smoke_run.sh for the stock-vs-
 * patched comparison.
 *
 * KNOWN RESULT (cron-20261022-0043): this REGISTER-consumer shape dies
 * to cse's plain value forwarding (y = y0 + t becomes y = y0 + a, the
 * copy goes dead, delete_dead_from_cse takes the subtract with it) -
 * the guards do not and should not save it; the store-consumer shape
 * (cc1_smoke2.c) is the one the milestone-3 guard is aimed at.
 */

extern long a;
extern long y0;

long cc1_smoke1 (void)
{
    long t = a;
    long x = t - t;
    long y = y0;
    y = y + t;
    return y;
}
