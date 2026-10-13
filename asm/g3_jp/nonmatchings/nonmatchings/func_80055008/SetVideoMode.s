.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching SetVideoMode, 0x18

glabel SetVideoMode
    /* 35808 80055008 0980023C */  lui        $v0, %hi(video_mode)
    /* 3580C 8005500C 5076428C */  lw         $v0, %lo(video_mode)($v0)
    /* 35810 80055010 0980013C */  lui        $at, %hi(video_mode)
    /* 35814 80055014 507624AC */  sw         $a0, %lo(video_mode)($at)
    /* 35818 80055018 0800E003 */  jr         $ra
    /* 3581C 8005501C 00000000 */   nop
endlabel SetVideoMode
