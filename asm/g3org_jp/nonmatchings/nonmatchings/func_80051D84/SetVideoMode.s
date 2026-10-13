.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching SetVideoMode, 0x18

glabel SetVideoMode
    /* 32584 80051D84 0A80023C */  lui        $v0, %hi(video_mode)
    /* 32588 80051D88 9843428C */  lw         $v0, %lo(video_mode)($v0)
    /* 3258C 80051D8C 0A80013C */  lui        $at, %hi(video_mode)
    /* 32590 80051D90 984324AC */  sw         $a0, %lo(video_mode)($at)
    /* 32594 80051D94 0800E003 */  jr         $ra
    /* 32598 80051D98 00000000 */   nop
endlabel SetVideoMode
