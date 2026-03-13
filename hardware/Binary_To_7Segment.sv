`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11/13/2025 10:32:19 PM
// Design Name: 
// Module Name: Binary_To_7Segment
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

module Binary_To_7Segment (
    input  logic       i_Clk,       
    input  logic [3:0] i_Binary_Num,
    output logic       o_Segment_A,
    output logic       o_Segment_B,
    output logic       o_Segment_C,
    output logic       o_Segment_D,
    output logic       o_Segment_E,
    output logic       o_Segment_F,
    output logic       o_Segment_G
);

    logic [6:0] r_segments;  

    always_comb begin
        unique case (i_Binary_Num)
            4'h0: r_segments = 7'b0111111; 
            4'h1: r_segments = 7'b0000110; 
            4'h2: r_segments = 7'b1011011; 
            4'h3: r_segments = 7'b1001111; 
            4'h4: r_segments = 7'b1100110; 
            4'h5: r_segments = 7'b1101101;
            4'h6: r_segments = 7'b1111101; 
            4'h7: r_segments = 7'b0000111; 
            4'h8: r_segments = 7'b1111111; 
            4'h9: r_segments = 7'b1101111; 
            4'hA: r_segments = 7'b1110111; 
            4'hB: r_segments = 7'b1111100; 
            4'hC: r_segments = 7'b0111001; 
            4'hD: r_segments = 7'b1011110; 
            4'hE: r_segments = 7'b1111001; 
            4'hF: r_segments = 7'b1110001; 
            default: r_segments = 7'b0000000; 
        endcase
    end

    always_comb begin
        o_Segment_A = r_segments[0];
        o_Segment_B = r_segments[1];
        o_Segment_C = r_segments[2];
        o_Segment_D = r_segments[3];
        o_Segment_E = r_segments[4];
        o_Segment_F = r_segments[5];
        o_Segment_G = r_segments[6];
    end

endmodule
