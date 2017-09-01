d3.selection.prototype.moveToFront = function() {
    return this.each(function() {
        this.parentNode.appendChild(this);
    });
};


var gp_scale = 0.65;

var gp_graph = {},
    gp_link, gp_node;

function loadGenepools() {
    if (jQuery.isEmptyObject(gp_graph)) {
        d3.json(webserviceHost + "genepoolNetworks", function(error, genepoolNetwork) {
            gp_graph.nodes = genepoolNetwork[0];
            gp_graph.links = genepoolNetwork[1];
            //console.log(gp_graph);
            updateGenepools(gp_graph);
        });
    } else {

        updateGenepools(gp_graph);

    }
}

if (!recordingID) {
  loadGenepools();
}

var gp_svg = d3.select("svg").append("g")
.attr("class", "genepools")
.on("mouseover", gpBGMouseover);


var gp_colors = d3.scaleOrdinal(d3.schemeCategory20);


var gp_simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) {
        return d.id;
    }))
    .force("charge", d3.forceManyBody().strength(-3)) //-25
    .force("collide", d3.forceCollide(2+ (12 * gp_scale))) //12
    .force("center", d3.forceCenter(width / 2, height / 2));


gp_simulation.force("link").strength(1)
    .distance(function(d) {
        return 10.0 * d.distance * gp_scale;
    });


function updateGenepools(gp_graph) {

    gp_link = gp_svg.append("g")
        .attr("class", "gp_links")
        .selectAll("line")
        .data(gp_graph.links)
        .enter().append("line")
        .attr("stroke-width",function(d) {
            return 5.0 * (1.0 - d.distance) * gp_scale;
        });
    gp_node = gp_svg.append("g")
        .attr("class", "gp_nodes")
        .selectAll("circle")
        .data(gp_graph.nodes)
        .enter().append("g")
        .attr("id", function(d) {
            return "Recording_" + d.recordingID;
        })
        .attr("visibility", function(d) {
            if (!d.terminal) {
                return "hidden";
            } else {
                return "";
            }
        })
        .on("mouseover", gpMouseover)
        .on("mouseleave", gpMouseOut)
        .on("click", gpClick);

    gp_node.append("circle")
        .attr("r", 13  * gp_scale)
        .attr("cx", 0)
        .attr("cy", 5)
        //.attr("pointer-events", "none")
        .attr("class", "gp_recording")
        .attr("stroke-width", 0)
        .attr("opacity",function(d) {
            return 1;//0.1 + 2 * d.interactivity;
        })
        .attr("fill", function(d) {
            var grayValue = parseInt((2 * d.interactivity) * 255);
            return "rgb(" +grayValue+ "," +grayValue+ "," +grayValue+ ")"
        });

        //#5c787d

    gp_node.append("circle")
        .attr("r", 6  * gp_scale)
        .attr("cx", -4)
        .attr("cy", 5)
        .attr("pointer-events", "none")
        .attr("fill", function(d) {
            return gp_colors(d.player1);
        });

    gp_node.append("circle")
        .attr("r", 6  * gp_scale)
        .attr("cx", 4)
        .attr("cy", 5)
        .attr("pointer-events", "none")
        .attr("fill", function(d) {
            return gp_colors(d.player2);
        });

      // gp_node.append("text")
      //       .attr("class","id-label")
      //       .attr('transform', function(d) {
      //           return 'translate(14, 8)';
      //       })
      //       .attr("opacity", "1").text(function(d) {
      //           return d.recordingID;
      //       });

    gp_simulation
        .nodes(gp_graph.nodes)
        .on("tick", ticked);

    gp_simulation.force("link").links(gp_graph.links);

    gp_simulation.alphaTarget(0.99);

    var gp_tAnimation = d3.timer(function(elapsed) {
        gp_simulation.force("charge").strength(-8 + elapsed / 1000);
        gp_simulation.alphaTarget(1.0 - elapsed / 30000);
        if (elapsed > 6000) { //6000
            gp_tAnimation.stop();
            //simulation.force("charge").strength(-2);
            gp_simulation.alphaTarget(0);
        }
    }, 500);
}

var gp_recordingInfo = {};


function gpMouseOut(d) {
    d3.select(this).style("cursor", "default");
    var thisNode = d3.select($(this).children().select(".gp_recording").get(0))
    thisNode.transition().duration(100).attr("stroke-width", "0");

    d3.select("#Recording_" + d.recordingID).transition().duration(100).select("text.gp_hover").remove();
    gp_node.transition().duration(100).style("opacity", "1.0");
    gp_link.transition().duration(100).style("opacity", "1.0");
    mouseoverState = undefined;
}

var mouseoverState;

function gpBGMouseover(d) {
  //d3.selectAll("text.gp_hover").remove();
}

function gpMouseover(d) {
    if (mouseoverState == undefined) {
        d3.select(this).style("cursor", "pointer");
        var thisNode = d3.select($(this).children().select(".gp_recording").get(0))

        thisNode.transition().duration(100).attr("stroke-width", 2.0  * gp_scale);

        d3.select(this).moveToFront();

        gp_node.transition().duration(100).style("opacity", function(n) {
            if (d.recordingID == n.recordingID) {
                return 1.0;
            } else {
                return 0.3;
            }
        });

        gp_link.transition().duration(100).style("opacity", "0.2");

        if (jQuery.isEmptyObject(gp_recordingInfo[d.recordingID])) {
            d3.json(webserviceHost + "recordings/" + d.recordingID, function(error, gp_recording) {
                gp_recordingInfo[d.recordingID] = gp_recording[0];
                showRecordingInfo(d.recordingID);
            });
        } else {
            showRecordingInfo(d.recordingID);
        }
        mouseoverState = d.recordingID;
    }
}

function showRecordingInfo(recordingID) {
    selectedRecording = gp_recordingInfo[recordingID];
    if (d3.select("#Recording_" + recordingID).select("text.gp_hover").empty() == true) {;
        var textbox = d3.select("#Recording_" + recordingID).append("text")
            .attr("class", "gp_hover")
            .attr('transform', function(d) {
                return 'translate(16, 1)';
            })
            .attr("opacity", "1");



        textbox.append("tspan").attr("x", 0).attr("y", 14).attr("class", "gp_small")
            .text("Player " + selectedRecording['tracks'][0]['playerKey'] + " (" + selectedRecording['tracks'][0]['playerInstrument'] + "), Player " + selectedRecording['tracks'][1]['playerKey'] + " (" + selectedRecording['tracks'][1][
                'playerInstrument'
            ] + ")");

          textbox.append("tspan").attr("x", 0).attr("y", 0).attr("class", "gp_strong")
                .text("Improvisation " + recordingID);

        //textbox.transition().duration(100).attr("opacity", "1");
    }

}

function resetGenepoolVis() {
    selectedFromGenepools = false;
}
var selectedFromGenepools = false;

function gpClick(d) {
    //console.log("click");
    gp_simulation.stop();
    d3.select("#Recording_" + d.recordingID).select("text.gp_hover").remove();
    var thisNode = d3.select($(this).children().select(".gp_recording").get(0))
    thisNode.attr("stroke-width", "0");

    gp_link.transition("linkFadeOut").duration(500).style("opacity", 0);
    d3.select(this).transition("scale").duration(1000).attr("transform","translate(" + width/2 + ", " + (height/2 - 100) + "),scale(30)");

    gp_node.transition("nodesFadeOut").duration(1500).style("opacity","0");

    //.on("end", gp_loadRecording(d.recordingID));
    selectedFromGenepools = true;
    var t = d3.timer(function(elapsed) {
      $("[recordingid=" + d.recordingID + "]").trigger("click");
      //gp_svg.selectAll("*").transition("remove").delay(500).duration(1000).remove();
      t.stop();
    }, 400);



}

function ticked() {

    gp_node.attr("transform", function(d) {
        return "translate(" + (Math.max(15, Math.min(width - 15, d.x)) - 0) + "," + (Math.max(10, Math.min(height - 20, d.y)) - 0) + ")";
    });

    gp_node.attr("cx", function(d) {
            return d.x = Math.max(15, Math.min(width - 15, d.x));
        })
        .attr("cy", function(d) {
            return d.y = Math.max(10, Math.min(height - 20, d.y));
        });

    gp_link
        .attr("x1", function(d) {
            return d.source.x;
        })
        .attr("y1", function(d) {
            return d.source.y;
        })
        .attr("x2", function(d) {
            return d.target.x;
        })
        .attr("y2", function(d) {
            return d.target.y;
        });

}

var radius = 13  * gp_scale;
var gp_selection = [];

d3.select("svg").on( "mousedown", function() {
    var p = d3.mouse( this);
    var svg = d3.select("svg");
    svg.append( "rect")
    .attr("ry",6)
    .attr("rx",6)
    .attr("class","selection")
    .attr("x",p[0])
    .attr("y",p[1])
    .attr("width",0)
    .attr("height",0);
})
.on( "mousemove", function() {
    var s = d3.select("svg").select( "rect.selection");

    if( !s.empty()) {
        var p = d3.mouse( this),
            d = {
                x       : parseInt( s.attr( "x"), 10),
                y       : parseInt( s.attr( "y"), 10),
                width   : parseInt( s.attr( "width"), 10),
                height  : parseInt( s.attr( "height"), 10)
            },
            move = {
                x : p[0] - d.x,
                y : p[1] - d.y
            }
        ;

        if( move.x < 1 || (move.x*2<d.width)) {
            d.x = p[0];
            d.width -= move.x;
        } else {
            d.width = move.x;
        }

        if( move.y < 1 || (move.y*2<d.height)) {
            d.y = p[1];
            d.height -= move.y;
        } else {
            d.height = move.y;
        }

        s.attr("x",d.x)
        .attr("y",d.y)
        .attr("width",d.width)
        .attr("height",d.height);

            // deselect all temporary selected state objects
        d3.selectAll('.gp_recording').classed( "gp-selected", false);
        gp_selection = [];
        if (gp_node!= undefined) {
          gp_node.each( function( state_data, i) {
              if(
                  !d3.select(this).classed( "selected") &&
                      // inner circle inside selection frame
                  state_data.x-radius>=d.x && state_data.x+radius<=d.x+d.width &&
                  state_data.y-radius>=d.y && state_data.y+radius<=d.y+d.height
              ) {
                  var thisNode = d3.select($(this).children().select(".gp_recording").get(0))
                  d3.select( this.parentNode).classed( "selection", true);
                  thisNode.classed( "gp-selected", true);

                  if (state_data.terminal) {
                    gp_selection.push(state_data.recordingID);
                  }
              }
          });
        }

    }
})
.on( "mouseup", function() {
       // remove selection frame
    d3.select("svg").selectAll( "rect.selection").remove();

        // remove temporary selection marker class
    d3.selectAll('.gp_recording').classed( "gp-selected", false);
    console.log(JSON.stringify(gp_selection));
});

// .on( "mouseout", function() {
//     if( d3.event.relatedTarget.tagName=='HTML') {
//             // remove selection frame
//         d3.select("svg").selectAll( "rect.selection").remove();
//
//             // remove temporary selection marker class
//         d3.selectAll( 'g.state.selection').classed( "selection", false);
//     }
// });
