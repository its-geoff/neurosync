`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/21/2026 12:47:56 PM
// Design Name: 
// Module Name: VGA_640x480_Timing
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module VGA_640x480_Timing (
    input  logic        i_Clock,    
    input  logic        i_Reset,
    output logic        o_HSync,
    output logic        o_VSync,
    output logic [9:0]  o_X,        //current pixel column (0-639 valid)
    output logic [9:0]  o_Y,        //current pixel row    (0-479 valid)
    output logic        o_Active    //high when in visible area
);

    //640x480 @ 60 Hz  (pixel clock = 25.175 MHz, we use 25 MHz CE)
    //Horizontal: 640 visible + 16 FP + 96 sync + 48 BP = 800 total
    //Vertical:   480 visible +  10 FP +  2 sync + 33 BP = 525 total

    localparam H_VISIBLE = 640, H_FP = 16, H_SYNC = 96, H_BP = 48;
    localparam V_VISIBLE = 480, V_FP = 10, V_SYNC =  2, V_BP = 33;
    localparam H_TOTAL   = H_VISIBLE + H_FP + H_SYNC + H_BP; 
    localparam V_TOTAL   = V_VISIBLE + V_FP + V_SYNC + V_BP; 

    logic [1:0] pix_div;
    logic       pix_ce;
    always_ff @(posedge i_Clock) begin
        if (i_Reset) pix_div <= 2'd0;
        else         pix_div <= pix_div + 2'd1;
    end
    assign pix_ce = (pix_div == 2'd3); 

    logic [9:0] h_cnt;
    always_ff @(posedge i_Clock) begin
        if (i_Reset)
            h_cnt <= '0;
        else if (pix_ce)
            h_cnt <= (h_cnt == H_TOTAL - 1) ? '0 : h_cnt + 1'b1;
    end

    logic [9:0] v_cnt;
    always_ff @(posedge i_Clock) begin
        if (i_Reset)
            v_cnt <= '0;
        else if (pix_ce && (h_cnt == H_TOTAL - 1))
            v_cnt <= (v_cnt == V_TOTAL - 1) ? '0 : v_cnt + 1'b1;
    end

    assign o_HSync  = ~((h_cnt >= H_VISIBLE + H_FP) &&
                        (h_cnt <  H_VISIBLE + H_FP + H_SYNC));
    assign o_VSync  = ~((v_cnt >= V_VISIBLE + V_FP) &&
                        (v_cnt <  V_VISIBLE + V_FP + V_SYNC));
    assign o_Active = (h_cnt < H_VISIBLE) && (v_cnt < V_VISIBLE);
    assign o_X      = h_cnt;
    assign o_Y      = v_cnt;

endmodule