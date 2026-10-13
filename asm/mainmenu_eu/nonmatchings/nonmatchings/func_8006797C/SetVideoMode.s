.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching SetVideoMode, 0x18

glabel SetVideoMode
    /* 4817C 8006797C 0B80023C */  lui        $v0, %hi(video_mode)
    /* 48180 80067980 7044428C */  lw         $v0, %lo(video_mode)($v0)
    /* 48184 80067984 0B80013C */  lui        $at, %hi(video_mode)
    /* 48188 80067988 704424AC */  sw         $a0, %lo(video_mode)($at)
    /* 4818C 8006798C 0800E003 */  jr         $ra
    /* 48190 80067990 00000000 */   nop
endlabel SetVideoMode
