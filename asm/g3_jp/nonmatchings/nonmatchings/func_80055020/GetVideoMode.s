.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching GetVideoMode, 0x10

glabel GetVideoMode
    /* 35820 80055020 0980023C */  lui        $v0, %hi(video_mode)
    /* 35824 80055024 5076428C */  lw         $v0, %lo(video_mode)($v0)
    /* 35828 80055028 0800E003 */  jr         $ra
    /* 3582C 8005502C 00000000 */   nop
endlabel GetVideoMode
