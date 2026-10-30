/* Probe round 2: which shape gives retail's load/store interleave?
 * D: ctrl as struct pointer (MEM_IN_STRUCT_P loads) + scalar stores
 * E: ctrl as volatile pointer + scalar stores
 * F: struct loads + struct-member stores */
struct Ctl { unsigned long f; };
struct Gs { unsigned long e24, d64, e20, d72, d71; };
extern struct Gs gs;

void probeD(struct Ctl *ctrl)
{
    if ((long)ctrl->f >= 0) {
        gs.e24 = (ctrl->f >> 3) & 3;
        gs.d64 = (ctrl->f >> 5) & 1;
        gs.e20 = (ctrl->f >> 6) & 1;
        gs.d72 = (ctrl->f >> 9) & 7;
        gs.d71 = (ctrl->f >> 30) & 1;
    }
}

void probeE(volatile unsigned long *ctrl)
{
    if ((long)*ctrl >= 0) {
        gs.e24 = (*ctrl >> 3) & 3;
        gs.d64 = (*ctrl >> 5) & 1;
        gs.e20 = (*ctrl >> 6) & 1;
        gs.d72 = (*ctrl >> 9) & 7;
        gs.d71 = (*ctrl >> 30) & 1;
    }
}

void probeF(struct Ctl *ctrl)
{
    struct Gs *o = &gs;
    if ((long)ctrl->f >= 0) {
        o->e24 = (ctrl->f >> 3) & 3;
        o->d64 = (ctrl->f >> 5) & 1;
        o->e20 = (ctrl->f >> 6) & 1;
        o->d72 = (ctrl->f >> 9) & 7;
        o->d71 = (ctrl->f >> 30) & 1;
    }
}
